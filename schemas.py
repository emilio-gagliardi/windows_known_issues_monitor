from pydantic import BaseModel
from datetime import datetime
from typing import Optional

print("Schemas module loaded successfully")


class URLBase(BaseModel):
    url: str


class URLCreate(URLBase):
    pass


class URL(URLBase):
    id: int

    class Config:
        from_attributes = True


print("URL schemas defined")


class ScrapeBase(BaseModel):
    timestamp: datetime
    content: str
    scrape_type: Optional[str] = None
    scrape_comment: Optional[str] = None
    create_alert: Optional[bool] = False


class ScrapeCreate(ScrapeBase):
    url_id: int


class Scrape(ScrapeBase):
    id: int
    url_id: int

    class Config:
        from_attributes = True  # Changed from orm_mode = True


class ScrapeUpdate(BaseModel):
    scrape_type: Optional[str] = None
    scrape_comment: Optional[str] = None
    create_alert: Optional[bool] = None


print("Scrape schemas defined")


class ChangeBase(BaseModel):
    change_type: str
    details: str


class Change(ChangeBase):
    id: int
    scrape_id: int

    class Config:
        from_attributes = True


# Add a test function to verify schema creation
def test_schemas():
    test_url = URL(
        id=1,
        url="https://learn.microsoft.com/en-us/windows/release-health/status-windows-server-2022#known-issues",
    )
    test_scrape = Scrape(
        id=1, url_id=1, timestamp=datetime.now(), content="Test content"
    )
    test_change = Change(
        id=1,
        scrape_id=1,
        change_type="Test",
        details="Test details",
    )
    print(f"Test URL: {test_url}")
    print(f"Test Scrape: {test_scrape}")
    print(f"Test Change: {test_change}")


# Run the test function
test_schemas()
