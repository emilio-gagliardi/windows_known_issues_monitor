import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from urllib.parse import urlparse
from collections import defaultdict

from app import schemas
from app.database import get_db, engine, SessionLocal, Base
from app.scraper import scrape_url, get_latest_scrape, periodic_scrape
from app.schemas import (
    URLBase as URLSchema,
    Scrape as ScrapeSchema,
    ScrapeCreate,
)
from app.models import (
    URL as URLModel,
    Scrape as ScrapeModel,
)
from app.url_repository import URLRepository

import hashlib

# import threading
import json
from datetime import datetime, timedelta
import os
import re
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

load_dotenv()
# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

url_repo = URLRepository()


async def send_email(subject: str, body: dict, recipients: list[str]):
    """
    Sends an email using SendGrid API with the specified subject, body, and recipients.

    Parameters:
        subject (str): The subject of the email.
        body (dict): A dictionary containing URLs as keys and a list of scrapes as values.
        recipients (list[str]): A list of email addresses to send the email to.

    Returns:
        Response: The response object from SendGrid API after sending the email.

    Raises:
        Exception: If an error occurs during the email sending process.

    Note:
        The body dictionary should have URLs as keys and a list of scrape objects as values.
        Each scrape object should have attributes 'scrape_type', 'scrape_comment', and 'content'.
    """
    message = Mail(
        from_email=os.getenv("SENDGRID_FROM_EMAIL"),
        to_emails=recipients,
        subject=subject,
    )
    email_content = ["New scrapes found:<br><br>"]
    for url, scrapes in body.items():

        link_text = process_url_for_title(url)
        email_content.append(f'Product: <a href="{url}">{link_text}</a>')

        for scrape in scrapes:
            email_content.append("Known Issues:")
            email_content.append(format_scrape_content(scrape))
            email_content.append(f"Scrape Type: {scrape.scrape_type}")
            email_content.append(f"Scrape Comment: {scrape.scrape_comment}")
            email_content.append("---")

    email_body = "<br>".join(email_content)
    message.add_content(Content("text/html", email_body))
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        logger.info(f"Email sent. Status Code: {response.status_code}")
        return response
    except Exception as e:
        logger.info(f"Error sending email: {e}")
        return response


def format_scrape_content(scrape: ScrapeModel) -> str:
    """
    Format the scrape content from a ScrapeModel object into a human-readable string.

    Parameters:
        scrape (ScrapeModel): The ScrapeModel object containing the content to be formatted.

    Returns:
        str: A formatted string representing the content of the scrape, including last updated time, summary, status, and originating update.

    If the content of the scrape cannot be parsed as JSON, an error message is returned.
    """
    try:
        content_dict = json.loads(scrape.content)
        known_issues = content_dict.get("known_issues", {}).get("row", {})

        formatted_content = (
            f"Last updated: {known_issues.get('Last updated', 'N/A')}\n"
            f"Summary:\n{known_issues.get('Summary', 'N/A')}\n"
            f"Status: {known_issues.get('Status', 'N/A')}\n"
            f"Originating update: {known_issues.get('Originating update', 'N/A')}\n"
        )
        return formatted_content
    except json.JSONDecodeError:
        return "Error: Unable to parse scrape content"


def process_url_for_title(url):
    """
    Process the URL to extract a title.

    Parameters:
        url (str): The URL from which to extract the title.

    Returns:
        str: The processed title extracted from the URL.
    """
    # Parse the URL
    parsed_url = urlparse(url)

    # Get the path
    path = parsed_url.path

    # Remove 'status' from the path
    path = path.replace("status-", "").replace("/status/", "")

    # Split the path and get the last part
    parts = path.split("/")
    last_part = (
        parts[-1] if parts[-1] else parts[-2]
    )  # Use second to last if last is empty

    # Remove file extension if present
    last_part = re.sub(r"\.[^.]+$", "", last_part)

    # Replace hyphens with spaces and capitalize each word
    title = " ".join(word.capitalize() for word in last_part.split("-"))

    return title


def process_scraped_data(
    db: Session, db_url: URLModel, scraped_data: dict
) -> list[ScrapeModel]:
    """
    Process the scraped data and create new ScrapeModel instances for each row of known issues.

    Parameters:
        db (Session): The database session to perform database operations.
        db_url (URLModel): The URLModel object representing the URL being scraped.
        scraped_data (dict): The scraped data containing information about known issues.

    Returns:
        list[ScrapeModel]: A list of newly created ScrapeModel instances for the scraped data rows.
    """
    new_scrapes = []
    if "known_issues" in scraped_data and "row" in scraped_data["known_issues"]:
        for known_issue_row in scraped_data["known_issues"]["row"]:
            row_data = {
                "known_issues": {
                    "header": scraped_data["known_issues"]["header"],
                    "row": known_issue_row,
                },
            }
        logger.info(f"Row data to be stored: {json.dumps(row_data, indent=2)}")

        content_hash = hashlib.md5(json.dumps(row_data).encode()).hexdigest()
        existing_scrape = (
            db.query(ScrapeModel)
            .filter(
                and_(
                    ScrapeModel.url_id == db_url.id,
                    ScrapeModel.hash == content_hash,
                )
            )
            .order_by(desc(ScrapeModel.timestamp))
            .first()
        )

        if existing_scrape:
            logger.info(
                f"Duplicate scrape found for row. Skipping creation for hash {content_hash}"
            )
            # new_scrapes.append(existing_scrape)
        else:
            # logger.info(f"Creating new scrape for row with hash {content_hash}")
            new_scrape = ScrapeModel(
                url_id=db_url.id,
                content=json.dumps(row_data),
                timestamp=datetime.now(timezone.utc),
                scrape_type=None,
                scrape_comment=None,
                create_alert=False,
                hash=content_hash,
            )
            db.add(new_scrape)
            db.flush()
            new_scrapes.append(new_scrape)

    return new_scrapes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous function to manage the lifespan of the FastAPI application.

    This function handles the startup, initialization, and shutdown of the application.
    During startup, it creates all database tables if they do not exist, loads the URL repository cache,
    scrapes all URLs, sets up a scheduler to run the scraping task daily at a specific time in a specified timezone,
    and starts the scheduler.

    Parameters:
        app (FastAPI): The FastAPI application instance.

    Raises:
        SQLAlchemyError: If an error occurs during the application lifespan related to the database connection or cache loading process.

    Yields:
        None

    Returns:
        None
    """
    try:
        # Startup
        # logger.info("Creating all database tables if they do not exist.")
        Base.metadata.create_all(bind=engine)

        def sync_load_cache():
            with SessionLocal() as session:
                # logger.info("Loading URL repository cache.")
                url_repo.load_cache(session)

        # Run the synchronous function in a thread pool
        await asyncio.to_thread(sync_load_cache)
        logger.info("URL repository loaded into cache.")
        enable_deep_scrape = (
            False  # Set this to True if you want to enable deep scraping
        )
        await scrape_all_urls_task(enable_deep_scrape)
        logger.info("Completed initial scraping of all URLs.")

        # Set up the scheduler
        scheduler = AsyncIOScheduler()

        # Schedule the task to run daily at 6:00 AM in your timezone
        scheduler.add_job(
            scrape_all_urls_task,
            CronTrigger(
                hour=6,
                minute=0,
                timezone=timezone(os.getenv("TIMEZONE", "America/Edmonton")),
            ),
            args=[enable_deep_scrape],
        )
        # Start the scheduler
        scheduler.start()

        yield

    except SQLAlchemyError as e:
        logger.error(
            f"An error occurred during the application lifespan: {e}. Please check the database connection or cache loading process."
        )
        raise
    finally:
        # Cleanup
        logger.info("Application shutdown.")


app = FastAPI(lifespan=lifespan)


@app.post("/urls/", response_model=schemas.URL)
def create_url(url: schemas.URLCreate, db: Session = Depends(get_db)):
    """
    Create a new URL.

    This endpoint allows you to create a new URL entry in the database.

    Args:
        url (schemas.URLCreate): The URL data to be created, defined by the URLCreate schema.
        db (Session): The database session, provided by dependency injection.

    Returns:
        schemas.URL: The created URL entry, defined by the URL schema.
    """
    # logger.info(f"Creating URL: {url.url}")
    db_url = url_repo.create_url(db, url.url)
    logger.info(f"Created URL: {db_url.id}")
    return db_url


@app.get("/urls/", response_model=list[schemas.URL])
def read_urls(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of URLs.

    This endpoint allows you to retrieve a list of URL entries from the database with pagination support.

    Args:
        skip (int, optional): The number of records to skip for pagination. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.
        db (Session): The database session, provided by dependency injection.

    Returns:
        List[schemas.URL]: A list of URL entries, defined by the URL schema.
    """
    # logger.info(f"Reading URLs with skip={skip} and limit={limit}")
    result = db.execute(select(URLModel).offset(skip).limit(limit))
    urls = result.scalars().all()
    logger.info(f"Retrieved {len(urls)} URLs")
    return urls


@app.get("/url/{url_id}", response_model=schemas.URL)
def read_url_by_id(url_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific URL by its ID.

    This endpoint allows you to retrieve a single URL entry from the database based on its ID.

    Args:
        url_id (int): The ID of the URL to retrieve.
        db (Session): The database session, provided by dependency injection.

    Returns:
        schemas.URL: The URL entry, defined by the URL schema.

    Raises:
        HTTPException: 404 error if the URL with the given ID is not found.
    """
    # logger.info(f"Fetching URL with id={url_id}")
    result = db.execute(select(URLModel).filter(URLModel.id == url_id))
    url = result.scalar_one_or_none()

    if url is None:
        logger.warning(f"URL with id={url_id} not found")
        raise HTTPException(status_code=404, detail="URL not found")

    # logger.info(f"Retrieved URL: {url.url}")
    return url


@app.post("/scrapes/", response_model=ScrapeSchema)
def create_scrape(scrape: ScrapeCreate, db: Session = Depends(get_db)):
    """
    Create a new scrape entry.

    This endpoint allows you to create a new scrape entry in the database. It checks if the content has changed by comparing the hash of the content.

    Args:
        scrape (schemas.ScrapeCreate): The scrape data to be created, defined by the ScrapeCreate schema.
        db (Session): The database session, provided by dependency injection.

    Returns:
        schemas.Scrape: The created scrape entry, defined by the Scrape schema.
        dict: A message indicating no changes detected if the content hash already exists for the given URL.
    """
    db_url = db.query(URLModel).filter(URLModel.id == scrape.url_id).first()
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    logger.info(f"Creating scrape for URL ID: {scrape.url_id}")
    content_hash = hashlib.md5(scrape.content.encode()).hexdigest()

    # Check if this hash already exists for the given URL
    existing_scrape = db.execute(
        select(ScrapeModel)
        .filter(ScrapeModel.url_id == scrape.url_id, ScrapeModel.hash == content_hash)
        .order_by(ScrapeModel.timestamp.desc())
    ).scalar_one_or_none()

    if existing_scrape:
        logger.info("No changes detected for the content")
        return {"message": "No changes detected"}

    new_scrape = ScrapeModel(
        url_id=scrape.url_id,
        content=scrape.content,
        timestamp=scrape.timestamp,
        scrape_type=scrape.scrape_type,
        scrape_comment=scrape.scrape_comment,
        create_alert=scrape.create_alert,
        hash=content_hash,
    )
    db.add(new_scrape)
    db.commit()
    db.refresh(new_scrape)
    return ScrapeSchema.model_validate(new_scrape)


@app.post("/scrape_and_create", response_model=list[ScrapeSchema])
async def scrape_and_create(
    url_data: URLSchema,
    db: Session = Depends(get_db),
    enable_deep_scrape: bool = False,
):
    try:
        # Step 1: Scrape the data
        scraped_data = await scrape_url(url_data, enable_deep_scrape=enable_deep_scrape)
        # logger.info(f"Scraped data structure: {json.dumps(scraped_data, indent=2)}")

        # Step 2: Check if the URL exists in the database
        db_url = db.query(URLModel).filter(URLModel.url == url_data.url).first()
        if not db_url:
            raise HTTPException(
                status_code=404, detail=f"URL with URL {url_data.url} not found"
            )

        # Step 3: Process scraped data and create new scrapes
        new_scrapes = process_scraped_data(db, db_url, scraped_data)

        # Step 4: Update last_scraped timestamp and commit changes
        if new_scrapes:
            db_url.last_scraped = new_scrapes[-1].timestamp
            db.commit()

        # Step 5: Return the new scrapes
        return [ScrapeSchema.model_validate(scrape) for scrape in new_scrapes]

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="scrape_and_create Database error: " + str(e)
        )
    finally:
        db.close()


@app.get("/scrapes/{scrape_id}", response_model=ScrapeSchema)
def read_scrape(scrape_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific scrape entry by ID.

    This endpoint allows you to retrieve a specific scrape entry from the database using its unique ID.

    Args:
        scrape_id (int): The unique identifier of the scrape entry to retrieve.
        db (Session): The database session, provided by dependency injection.

    Returns:
        schemas.Scrape: The scrape entry, defined by the Scrape schema.

    Raises:
        HTTPException: If the scrape entry is not found, a 404 status code is returned with a "Scrape not found" detail.
    """
    # logger.info(f"Reading scrape with ID: {scrape_id}")
    scrape = db.execute(
        select(ScrapeModel).filter(ScrapeModel.id == scrape_id)
    ).scalar_one_or_none()

    if scrape is None:
        logger.error(f"Scrape not found for ID: {scrape_id}")
        raise HTTPException(status_code=404, detail="Scrape not found")
    return scrape


@app.get("/scrapes/", response_model=list[ScrapeSchema])
def read_all_scrapes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all scrape entries with pagination.

    This endpoint allows you to retrieve all scrape entries from the database with optional pagination.

    Args:
        skip (int): The number of entries to skip (default: 0).
        limit (int): The maximum number of entries to return (default: 100).
        db (Session): The database session, provided by dependency injection.

    Returns:
        List[schemas.Scrape]: A list of scrape entries, defined by the Scrape schema.
    """
    result = db.execute(select(ScrapeModel).offset(skip).limit(limit))
    return result.scalars().all()


@app.get("/scrapes/urlid/{url_id}", response_model=list[ScrapeSchema])
def read_scrapes_by_urlid(
    url_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """
    Retrieve scrape entries for a specific URL ID with pagination and sorting.

    This endpoint allows you to retrieve scrape entries from the database for a given URL ID with optional pagination,
    sorted by timestamp in descending order.

    Args:
        url_id (int): The unique identifier of the URL to filter scrapes by.
        skip (int): The number of entries to skip (default: 0).
        limit (int): The maximum number of entries to return (default: 100).
        db (Session): The database session, provided by dependency injection.

    Returns:
        List[schemas.Scrape]: A list of scrape entries for the specified URL ID, defined by the Scrape schema.
    """
    result = db.execute(select(ScrapeModel).filter(ScrapeModel.url_id == url_id))
    scrapes = result.scalars().all()

    # Parse "Last updated" from content and sort
    def parse_last_updated(scrape):
        try:
            content = json.loads(scrape.content)
            last_updated = (
                content["issue_details"]["row"]["History"]
                .split("Last updated: ")[1]
                .split(",")[0]
            )
            return datetime.strptime(last_updated, "%Y-%m-%d")
        except Exception as e:
            logger.exception(f"Error parsing date for scrape {scrape.id}: {str(e)}")
            logger.exception(f"Error parsing date for scrape {scrape.id}: {str(e)}")
            return datetime.min

    sorted_scrapes = sorted(scrapes, key=parse_last_updated, reverse=True)

    # Return the top 'limit' scrapes
    return sorted_scrapes[:limit]


@app.put("/scrapes/{scrape_id}", response_model=ScrapeSchema)
def update_scrape(
    scrape_id: int,
    scrape_update: schemas.ScrapeUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a specific scrape entry by ID.

    This endpoint allows you to update a specific scrape entry in the database using its unique ID.
    Only the fields provided in the update request will be modified.

    Args:
        scrape_id (int): The unique identifier of the scrape entry to update.
        scrape_update (schemas.ScrapeUpdate): The data to update the scrape entry with.
        db (Session): The database session, provided by dependency injection.

    Returns:
        schemas.Scrape: The updated scrape entry, defined by the Scrape schema.

    Raises:
        HTTPException: If the scrape entry is not found, a 404 status code is returned with a "Scrape not found" detail.
    """
    # logger.info(f"Updating scrape with ID: {scrape_id}")
    result = db.execute(select(ScrapeModel).filter(ScrapeModel.id == scrape_id))
    db_scrape = result.scalar_one_or_none()
    if db_scrape is None:
        logger.error(f"Scrape not found for ID: {scrape_id}")
        raise HTTPException(status_code=404, detail="Scrape not found")

    update_data = scrape_update.model_dump(exclude_unset=True)
    logger.info(f"Update data: {update_data}")
    for key, value in update_data.items():
        setattr(db_scrape, key, value)

    db.commit()
    db.refresh(db_scrape)
    logger.info(f"Updated scrape with ID: {db_scrape.id}")
    return db_scrape


@app.get("/flagged_scrapes/", response_model=list[ScrapeSchema])
def get_flagged_scrapes(db: Session = Depends(get_db)):
    """
    Retrieve all flagged scrape entries.

    This endpoint allows you to retrieve all scrape entries from the database where the 'create_alert' flag is set to True.

    Args:
        db (Session): The database session, provided by dependency injection.

    Returns:
        List[schemas.Scrape]: A list of flagged scrape entries, defined by the Scrape schema.
    """
    result = db.execute(select(ScrapeModel).filter(ScrapeModel.create_alert.is_(True)))
    return result.scalars().all()


@app.post("/scrape", response_model=dict)
async def scrape_endpoint(url_data: URLSchema, db: Session = Depends(get_db)):
    """
    Scrape a given URL and store the result in the database.

    This endpoint allows you to scrape the content of a specified URL and store the result in the database.
    The scraping logic is handled by the `scrape_url` function.

    Args:
        url (str): The URL to scrape.
        db (Session): The database session, provided by dependency injection.

    Returns:
        schemas.Scrape: The result of the scraping operation, as returned by the `scrape_url` function.
    """

    result = await scrape_url(url_data, db)
    return result


@app.get("/latest", response_model=ScrapeSchema)
def get_latest_endpoint(url: str, db: Session = Depends(get_db)):
    """
    Retrieve the latest scrape data for a given URL.

    This endpoint allows you to fetch the most recent scrape data for a specified URL from the database.

    Args:
        url (str): The URL to retrieve the latest scrape data for.
        db (Session): The database session, provided by dependency injection.

    Returns:
        schemas.Scrape: The latest scrape data for the specified URL.

    Raises:
        HTTPException: If no scrape data is found for the given URL.
    """
    result = get_latest_scrape(url, db)
    if result is None:
        raise HTTPException(status_code=404, detail="No scrape data found for this URL")
    return result


async def scrape_all_urls_task(enable_deep_scrape: bool):
    logger.info(f"Starting scrape_all_urls_task with deep_scrape: {enable_deep_scrape}")
    db = SessionLocal()
    new_scrapes_dict = defaultdict(list)

    try:
        with SessionLocal() as db:
            url_models = db.query(URLModel).all()
            logger.info(f"Found {len(url_models)} URLs to scrape.")
            if not url_models:
                logger.warning("No URLs found in the database. No URLs to scrape.")
                return
        urls = [url_model.url for url_model in url_models]
        for url in urls:
            try:
                with SessionLocal() as url_session:
                    logger.info(f"Scraping [<-] {url}")
                    scrape_results = await scrape_and_create(
                        URLSchema(url=url), url_session, enable_deep_scrape
                    )
                    if scrape_results:
                        new_scrapes_dict[url].extend(scrape_results)
                    url_session.commit()
            except Exception as e:
                logger.error(f"Error scraping {url.url}: {str(e)}")
                continue

        # After all URLs are scraped, send email if there are new scrapes
        if new_scrapes_dict:
            subject = "New Known Issues Published!"
            recipients = ["emilio.gagliardi@gmail.com"]
            try:
                await send_email(subject, new_scrapes_dict, recipients)
                logger.info("Email sent successfully.")
            except Exception as e:
                logger.error(f"Error sending email: {str(e)}")
                logger.error(traceback.format_exc())
        else:
            logger.info("No new scrapes found. No email sent.")

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        db.close()


@app.post("/scrape_all", status_code=202)
async def trigger_scrape_all(
    background_tasks: BackgroundTasks, enable_deep_scrape: bool = Query(False)
):
    logger.info(f"Received request with enable_deep_scrape: {enable_deep_scrape}")
    background_tasks.add_task(scrape_all_urls_task, enable_deep_scrape)
    return {"message": "Scraping process started", "deep_scrape": enable_deep_scrape}
