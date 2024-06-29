import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import URL, Scrape
from app.database import get_db
from datetime import datetime, timezone, timedelta


async def scrape_url(url: str, db: AsyncSession = None) -> dict:
    print(f"Starting to scrape URL: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        print(f"Navigating to {url}")
        await page.goto(url)

        print("Waiting for tables to load")
        await page.wait_for_selector("table")

        content = await page.content()
        await browser.close()

        print("Parsing content with BeautifulSoup")
        soup = BeautifulSoup(content, "html.parser")

        scraped_data = {}

        # Scrape the first table (Known issues)
        print("Extracting data from the first table (Known issues)")
        known_issues_header = soup.select_one("h2#known-issues")
        known_issues_table = soup.select_one("table")
        if known_issues_header and known_issues_table:
            first_row = known_issues_table.select_one("tbody tr")
            if first_row:
                known_issues_data = {
                    "Summary": (
                        first_row.select_one("td:nth-of-type(1)").text.strip()
                        if first_row.select_one("td:nth-of-type(1)")
                        else ""
                    ),
                    "Originating update": (
                        first_row.select_one("td:nth-of-type(2)").text.strip()
                        if first_row.select_one("td:nth-of-type(2)")
                        else ""
                    ),
                    "Status": (
                        first_row.select_one("td:nth-of-type(3)").text.strip()
                        if first_row.select_one("td:nth-of-type(3)")
                        else ""
                    ),
                    "Last updated": (
                        first_row.select_one("td:nth-of-type(4)").text.strip()
                        if first_row.select_one("td:nth-of-type(4)")
                        else ""
                    ),
                }
                scraped_data["known_issues"] = {
                    "header": known_issues_header.text.strip(),
                    "first_row": known_issues_data,
                }

        # Scrape the second table (Issue details)
        print("Extracting data from the second table (Issue details)")
        issue_details_header = soup.select_one("h2#issue-details")
        latest_month = soup.select_one("h3[id^='']")
        issue_details_tables = soup.select("table")

        if issue_details_header and len(issue_details_tables) > 1:
            issue_details_table = issue_details_tables[1]  # Select the second table
            issue_details_rows = issue_details_table.select("tbody tr")
            if len(issue_details_rows) > 1:  # Ensure we have at least one data row
                issue_details_row = issue_details_rows[
                    1
                ]  # Select the first data row (index 1, as 0 is header)
                issue_details_data = {
                    "Status": (
                        issue_details_row.select_one("td:nth-of-type(1)").text.strip()
                        if issue_details_row.select_one("td:nth-of-type(1)")
                        else ""
                    ),
                    "Originating update": (
                        issue_details_row.select_one("td:nth-of-type(2)").text.strip()
                        if issue_details_row.select_one("td:nth-of-type(2)")
                        else ""
                    ),
                    "History": (
                        issue_details_row.select_one("td:nth-of-type(3)").text.strip()
                        if issue_details_row.select_one("td:nth-of-type(3)")
                        else ""
                    ),
                }
                scraped_data["issue_details"] = {
                    "header": issue_details_header.text.strip(),
                    "latest_month": latest_month.text.strip() if latest_month else "",
                    "first_row": issue_details_data,
                }

        print(f"Scraped data: {json.dumps(scraped_data, indent=2)}")

        if db:
            print("Storing scraped data in the database")
            db_url = await db.query(URL).filter(URL.url == url).first()
            if not db_url:
                db_url = URL(url=url)
                db.add(db_url)
                await db.commit()

            new_scrape = Scrape(
                url_id=db_url.id,
                content=json.dumps(scraped_data),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(new_scrape)
            await db.commit()
            print("Data stored in the database")

        return scraped_data


async def get_latest_scrape(url: str, db: AsyncSession) -> dict:
    print(f"Getting latest scrape for URL: {url}")
    db_url = await db.query(URL).filter(URL.url == url).first()
    if not db_url:
        print("URL not found in database")
        return None

    latest_scrape = (
        await db.query(Scrape)
        .filter(Scrape.url_id == db_url.id)
        .order_by(Scrape.timestamp.desc())
        .first()
    )
    if not latest_scrape:
        print("No scrapes found for this URL")
        return None

    print("Returning latest scrape data")
    return json.loads(latest_scrape.content)


async def periodic_scrape(db: AsyncSession):
    while True:
        print("Starting periodic scrape")
        try:
            # Fetch URLs that need to be scraped
            stmt = select(URL).where(
                (URL.last_scraped is None)
                | (URL.last_scraped < datetime.now(timezone.utc) - timedelta(hours=4))
            )
            result = await db.execute(stmt)
            urls_to_scrape = result.scalars().all()

            for url in urls_to_scrape:
                try:
                    await scrape_url(url.url, db)
                    url.last_scraped = datetime.now(timezone.utc)
                    await db.commit()
                except Exception as e:
                    print(f"Error scraping URL {url.url}: {str(e)}")
                    await db.rollback()

        except Exception as e:
            print(f"Error in periodic scrape: {str(e)}")

        # Wait for 1 hour before the next scrape
        await asyncio.sleep(3600)


async def test_scraper():
    url = "https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-22h2"
    print("Testing scraper function")
    result = await scrape_url(url)
    print("Scraping complete. Results:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(test_scraper())
