import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app import models
from app import schemas
from app.database import get_db, engine
from app.scraper import scrape_url, get_latest_scrape, periodic_scrape
from app.url_repository import URLRepository
import hashlib

url_repo = URLRepository()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifespan of a FastAPI application, handling startup and shutdown events.

    This function performs the following tasks:
    - On startup:
        - Creates all database tables defined in the models if they do not already exist.
        - Loads the URL repository cache.
        - Starts a periodic scraping task.
    - On shutdown:
        - Cancels the periodic scraping task.
        - Disposes of the database engine.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: This function is used as a context manager and does not return any value.
    """
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        await url_repo.load_cache(session)

    scrape_task = asyncio.create_task(periodic_scrape(AsyncSession(engine)))
    yield

    # Shutdown
    scrape_task.cancel()
    try:
        await scrape_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.post("/urls/", response_model=schemas.URL)
async def create_url(url: schemas.URLCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new URL.

    This endpoint allows you to create a new URL entry in the database.

    Args:
        url (schemas.URLCreate): The URL data to be created, defined by the URLCreate schema.
        db (AsyncSession): The database session, provided by dependency injection.

    Returns:
        schemas.URL: The created URL entry, defined by the URL schema.
    """
    db_url = await url_repo.create_url(db, url.url)
    return db_url


@app.get("/urls/", response_model=List[schemas.URL])
async def read_urls(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of URLs.

    This endpoint allows you to retrieve a list of URL entries from the database with pagination support.

    Args:
        skip (int, optional): The number of records to skip for pagination. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.
        db (AsyncSession): The database session, provided by dependency injection.

    Returns:
        List[schemas.URL]: A list of URL entries, defined by the URL schema.
    """
    result = await db.execute(select(models.URL).offset(skip).limit(limit))
    return result.scalars().all()


@app.post("/scrapes/", response_model=schemas.Scrape)
async def create_scrape(
    scrape: schemas.ScrapeCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create a new scrape entry.

    This endpoint allows you to create a new scrape entry in the database. It checks if the content has changed by comparing the hash of the content.

    Args:
        scrape (schemas.ScrapeCreate): The scrape data to be created, defined by the ScrapeCreate schema.
        db (AsyncSession): The database session, provided by dependency injection.

    Returns:
        schemas.Scrape: The created scrape entry, defined by the Scrape schema.
        dict: A message indicating no changes detected if the content hash already exists for the given URL.
    """

    content_hash = hashlib.md5(scrape.content.encode()).hexdigest()

    # Check if this hash already exists for the given URL
    existing_scrape = await db.execute(
        select(models.Scrape)
        .filter(
            models.Scrape.url_id == scrape.url_id, models.Scrape.hash == content_hash
        )
        .order_by(models.Scrape.timestamp.desc())
    )
    if existing_scrape.scalar_one_or_none():
        return {"message": "No changes detected"}

    db_scrape = models.Scrape(**scrape.dict(), hash=content_hash)
    db.add(db_scrape)
    await db.commit()
    await db.refresh(db_scrape)
    return db_scrape


@app.get("/scrapes/{scrape_id}", response_model=schemas.Scrape)
async def read_scrape(scrape_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific scrape entry by ID.

    This endpoint allows you to retrieve a specific scrape entry from the database using its unique ID.

    Args:
        scrape_id (int): The unique identifier of the scrape entry to retrieve.
        db (AsyncSession): The database session, provided by dependency injection.

    Returns:
        schemas.Scrape: The scrape entry, defined by the Scrape schema.

    Raises:
        HTTPException: If the scrape entry is not found, a 404 status code is returned with a "Scrape not found" detail.
    """
    result = await db.execute(
        select(models.Scrape).filter(models.Scrape.id == scrape_id)
    )
    scrape = result.scalar_one_or_none()
    if scrape is None:
        raise HTTPException(status_code=404, detail="Scrape not found")
    return scrape


@app.get("/scrapes/", response_model=List[schemas.Scrape])
async def read_all_scrapes(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Scrape).offset(skip).limit(limit))
    return result.scalars().all()


@app.get("/scrapes/urlid/{url_id}", response_model=List[schemas.Scrape])
async def read_scrapes_by_urlid(
    url_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.Scrape)
        .filter(models.Scrape.url_id == url_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@app.put("/scrapes/{scrape_id}", response_model=schemas.Scrape)
async def update_scrape(
    scrape_id: int,
    scrape_update: schemas.ScrapeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a specific scrape entry by ID.

    This endpoint allows you to update a specific scrape entry in the database using its unique ID.
    Only the fields provided in the update request will be modified.

    Args:
        scrape_id (int): The unique identifier of the scrape entry to update.
        scrape_update (schemas.ScrapeUpdate): The data to update the scrape entry with.
        db (AsyncSession): The database session, provided by dependency injection.

    Returns:
        schemas.Scrape: The updated scrape entry, defined by the Scrape schema.

    Raises:
        HTTPException: If the scrape entry is not found, a 404 status code is returned with a "Scrape not found" detail.
    """

    result = await db.execute(
        select(models.Scrape).filter(models.Scrape.id == scrape_id)
    )
    db_scrape = result.scalar_one_or_none()
    if db_scrape is None:
        raise HTTPException(status_code=404, detail="Scrape not found")

    update_data = scrape_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_scrape, key, value)

    await db.commit()
    await db.refresh(db_scrape)
    return db_scrape


@app.post("/changes/", response_model=schemas.Change)
async def create_change(
    change: schemas.ChangeBase, scrape_id: int, db: AsyncSession = Depends(get_db)
):
    db_change = models.Change(**change.dict(), scrape_id=scrape_id)
    db.add(db_change)
    await db.commit()
    await db.refresh(db_change)
    return db_change


@app.get("/changes/{scrape_id}", response_model=List[schemas.Change])
async def read_changes(scrape_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Change).filter(models.Change.scrape_id == scrape_id)
    )
    return result.scalars().all()


@app.get("/flagged_scrapes/")
async def get_flagged_scrapes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Scrape).filter(models.Scrape.create_alert.is_(True))
    )
    return result.scalars().all()


@app.post("/scrape")
async def scrape_endpoint(url: str, db: AsyncSession = Depends(get_db)):
    """
    Scrape a given URL and store the result in the database.

    This endpoint allows you to scrape the content of a specified URL and store the result in the database.
    The scraping logic is handled by the `scrape_url` function.

    Args:
        url (str): The URL to scrape.
        db (AsyncSession): The database session, provided by dependency injection.

    Returns:
        dict: The result of the scraping operation, as returned by the `scrape_url` function.
    """

    result = await scrape_url(url, db)
    return result


@app.get("/latest")
async def get_latest_endpoint(url: str, db: AsyncSession = Depends(get_db)):
    result = await get_latest_scrape(url, db)
    if result is None:
        return {"message": "No scrape data found for this URL"}
    return result
