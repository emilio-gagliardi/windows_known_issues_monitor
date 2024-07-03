# from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from sqlalchemy import text, func, DateTime

# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app import schemas
from app.models import URL as URLModel, Scrape as ScrapeModel
from app.schemas import URLBase as URLSchema, Scrape as ScrapeSchema
from app.database import SessionLocal, get_db

from datetime import datetime, timezone, timedelta
import time
import re
import asyncio
import logging

# from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def scrape_url_async(url: str):
    print(f"Starting to scrape URL: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        content = await page.content()
        await browser.close()
    return content


async def scrape_url(
    url_data: URLSchema,
    db: Session = None,
    enable_deep_scrape: bool = False,
) -> dict:
    logger.info(
        f"Starting scrape for URL: {url_data}, Deep scrape: {enable_deep_scrape}"
    )
    url = url_data.url
    content = await scrape_url_async(url)

    soup = BeautifulSoup(content, "html.parser")

    scraped_data = {}

    # Scrape the first table (Known issues)
    print("Extracting data from the first table (Known issues)")
    known_issues_header = soup.select_one("h2#known-issues")
    known_issues_table = soup.select_one("table")
    if known_issues_header and known_issues_table:
        rows = known_issues_table.select("tbody tr")
        # logger.info(f"BS Found HTML rows KNown Issues\n{rows}")
        known_issues_data = []
        for row in rows[:1] if not enable_deep_scrape else rows:
            data = {
                "Summary": (
                    row.select_one("td:nth-of-type(1)").text.strip()
                    if row.select_one("td:nth-of-type(1)")
                    else ""
                ),
                "Originating update": (
                    row.select_one("td:nth-of-type(2)").get_text(
                        separator=" | ", strip=True
                    )
                    if row.select_one("td:nth-of-type(2)")
                    else ""
                ),
                "Status": (
                    row.select_one("td:nth-of-type(3)").text.strip()
                    if row.select_one("td:nth-of-type(3)")
                    else ""
                ),
                "Last updated": (
                    row.select_one("td:nth-of-type(4)").text.strip()
                    if row.select_one("td:nth-of-type(4)")
                    else ""
                ),
            }
            known_issues_data.append(data)
        scraped_data["known_issues"] = {
            "header": (
                known_issues_header.text.strip()
                if known_issues_header
                else "Known issues"
            ),
            "row": known_issues_data,
        }

    return scraped_data


def get_latest_scrape(url: str, db: Session) -> dict:
    print(f"Getting latest scrape for URL: {url}")
    db_url = db.query(URLModel).filter(URLModel.url == url).first()
    if not db_url:
        print("URL not found in database")
        return None

    latest_scrape = (
        db.query(ScrapeModel)
        .filter(ScrapeModel.url_id == db_url.id)
        .order_by(ScrapeModel.timestamp.desc())
        .first()
    )
    if not latest_scrape:
        print("No scrapes found for this URL")
        return None

    print("Returning latest scrape data")
    return json.loads(latest_scrape.content)


async def periodic_scrape(stop_event):
    while not stop_event.is_set():
        print("Starting periodic scrape")
        try:
            async with SessionLocal as session:
                async with session.begin():
                    current_time = datetime.now(timezone.utc)
                    four_hours_ago = (current_time - timedelta(hours=4)).replace(
                        tzinfo=None
                    )

                    stmt = select(URLModel).where(
                        or_(
                            URLModel.last_scraped.is_(None),
                            func.timezone(text("'UTC'"), URLModel.last_scraped)
                            < func.timezone(
                                text("'UTC'"), func.cast(four_hours_ago, DateTime)
                            ),
                        )
                    )
                    result = await session.execute(stmt)
                    urls_to_scrape = result.scalars().all()

                    for url in urls_to_scrape:
                        try:
                            await scrape_url(url.url, session)
                            url.last_scraped = current_time
                            await session.commit()
                        except Exception as e:
                            print(f"Error scraping URL {url.url}: {str(e)}")
                            await session.rollback()

        except Exception as e:
            print(f"Error in periodic scrape: {str(e)}")

        await asyncio.sleep(14400)


def test_scraper():
    url = "https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-22h2"
    print("Testing scraper function")
    result = scrape_url(url)
    print("Scraping complete. Results:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    test_scraper()
