from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from sqlalchemy.ext.asyncio import AsyncSession
from models import URL, Scrape
from database import get_db
from datetime import datetime


async def scrape_url(url: str, db: AsyncSession) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)

        # Wait for the table to load
        await page.wait_for_selector("table")

        content = await page.content()
        await browser.close()

        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")

        # Extract the header
        header = soup.select_one("h2#known-issues").text.strip()

        # Extract the first row of the table body
        table = soup.select_one("table")
        first_row = table.select_one("tbody tr")

        # Extract data from the first row
        row_data = {
            "Summary": first_row.select_one("td:nth-of-type(1)").text.strip(),
            "Originating update": first_row.select_one(
                "td:nth-of-type(2)"
            ).text.strip(),
            "Status": first_row.select_one("td:nth-of-type(3)").text.strip(),
            "Last updated": first_row.select_one("td:nth-of-type(4)").text.strip(),
        }

        # Create a dictionary with the scraped data
        scraped_data = {"header": header, "first_row": row_data}

        # Store the scraped data in the database
        db_url = await db.query(URL).filter(URL.url == url).first()
        if not db_url:
            db_url = URL(url=url)
            db.add(db_url)
            await db.commit()

        new_scrape = Scrape(
            url_id=db_url.id,
            content=json.dumps(scraped_data),
            timestamp=datetime.utcnow(),
        )
        db.add(new_scrape)
        await db.commit()

        return scraped_data


async def get_latest_scrape(url: str, db: AsyncSession) -> dict:
    db_url = await db.query(URL).filter(URL.url == url).first()
    if not db_url:
        return None

    latest_scrape = (
        await db.query(Scrape)
        .filter(Scrape.url_id == db_url.id)
        .order_by(Scrape.timestamp.desc())
        .first()
    )
    if not latest_scrape:
        return None

    return json.loads(latest_scrape.content)
