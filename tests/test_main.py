import pytest
import asyncio
from httpx import AsyncClient
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.database import get_db, AsyncSessionLocal
from datetime import datetime


@pytest.fixture(scope="function")
async def async_session():
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# @pytest.fixture
# async def test_db():
#     """
#     Fixture to provide a test database session.

#     In a real-world scenario, this would set up a separate test database.
#     For now, we're using the regular database session.

#     Yields:
#         AsyncSession: An async database session for testing.
#     """
#     async for session in get_db():
#         yield session


@pytest.mark.asyncio
async def test_create_url(client):
    """
    Test the creation of a new URL through the API.

    This test sends a POST request to the /urls/ endpoint with a URL,
    and checks if the response is correct.
    """

    # Send a POST request to create a new URL
    response = await client.post(
        "/urls/",
        json={
            "url": "https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-21H2"
        },
    )

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200
    # Check if the returned URL matches the one we sent
    assert (
        response.json()["url"]
        == "https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-21H2"
    )


@pytest.mark.asyncio
async def test_read_urls(client):
    """
    Test reading all URLs from the API.

    This test sends a GET request to the /urls/ endpoint and checks
    if the response is a list of URLs.
    """

    # Send a GET request to retrieve all URLs
    response = await client.get("/urls/")

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200
    # Check if the response is a list (of URLs)
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_scrape(client):
    """
    Test the creation of a new scrape through the API.

    This test first creates a URL, then creates a scrape for that URL,
    and checks if the responses are correct.
    """

    # First, create a URL
    url_response = await client.post(
        "/urls/",
        json={
            "url": "https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-21H2"
        },
    )
    url_id = url_response.json()["id"]

    # Then, create a scrape for this URL
    scrape_data = {
        "url_id": url_id,
        "timestamp": datetime.now().isoformat(),
        "content": "Sample content",
        "create_alert": False,
    }
    # Send a POST request to create a new scrape
    response = await client.post("/scrapes/", json=scrape_data)

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200
    # Check if the returned url_id matches the one we sent
    assert response.json()["url_id"] == url_id


@pytest.mark.asyncio
async def test_read_all_scrapes(client):
    """
    Test reading all scrapes from the API.

    This test sends a GET request to the /scrapes/ endpoint and checks
    if the response is a list of scrapes.
    """
    response = await client.get("/scrapes/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_read_scrapes_by_urlid(client):
    # Assuming you have a valid url_id, replace 1 with an actual id
    response = await client.get("/scrapes/urlid/7")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_read_scrapes_by_scrapeid(client):
    # Assuming you have a valid scrape_id, replace 1 with an actual id
    response = await client.get("/scrapes/1")
    assert response.status_code == 200
    scrape_data = response.json()
    assert isinstance(scrape_data, dict)  # Check if it's a dictionary (single object)
    # Add more specific assertions about the scrape data
    assert "id" in scrape_data
    assert scrape_data["id"] == 1


@pytest.mark.asyncio
async def test_update_scrape(client):
    # First, create a URL
    url_response = await client.post(
        "/urls/",
        json={
            "url": "https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-21H2"
        },
    )
    assert url_response.status_code == 200, f"Failed to create URL: {url_response.text}"
    url_data = url_response.json()
    assert "id" in url_data, f"URL response doesn't contain 'id': {url_data}"
    url_id = url_data["id"]

    # Now, create a scrape
    scrape_response = await client.post(
        "/scrapes/",
        json={
            "url_id": url_id,
            "content": "Initial content",  # Changed to string
            "create_alert": False,
            "timestamp": datetime.now().isoformat(),  # Added timestamp
            "scrape_type": "manual",  # You might need to add this field
            "scrape_comment": "Test scrape",  # You might need to add this field
        },
    )
    assert (
        scrape_response.status_code == 200
    ), f"Failed to create scrape: {scrape_response.text}"
    scrape_data = scrape_response.json()
    print(f"Scrape creation response: {scrape_data}")  # Debug print
    assert "id" in scrape_data, f"Scrape response doesn't contain 'id': {scrape_data}"
    scrape_id = scrape_data["id"]

    # Update the scrape
    update_data = {
        "content": "Updated content",
        "create_alert": True,
        "scrape_comment": "Updated test scrape",
    }
    response = await client.put(f"/scrapes/{scrape_id}", json=update_data)

    assert response.status_code == 200, f"Failed to update scrape: {response.text}"
    updated_data = response.json()
    assert updated_data["content"] == "Updated content"
    assert updated_data["create_alert"] is True
    assert updated_data["scrape_comment"] == "Updated test scrape"


@pytest.mark.asyncio
async def test_create_change(client):
    """
    Test creating a change through the API.

    This test creates a change for a scrape and checks if the
    response is correct.
    """

    # First, create a URL and a scrape
    url_response = await client.post(
        "/urls/",
        json={
            "url": "https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-21H2"
        },
    )
    url_id = url_response.json()["id"]
    scrape_response = await client.post(
        "/scrapes/",
        json={"url_id": url_id, "data": {"key": "value"}, "create_alert": False},
    )
    scrape_id = scrape_response.json()["id"]

    # Now, create a change
    change_data = {
        "scrape_id": scrape_id,
        "field": "key",
        "old_value": "value",
        "new_value": "new_value",
    }
    response = await client.post("/changes/", json=change_data)

    assert response.status_code == 200
    assert response.json()["scrape_id"] == scrape_id


@pytest.mark.asyncio
async def test_read_changes():
    """
    Test reading all changes from the API.

    This test sends a GET request to the /changes/ endpoint and checks
    if the response is a list of changes.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/changes/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_flagged_scrapes():
    """
    Test retrieving flagged scrapes from the API.

    This test sends a GET request to the /scrapes/flagged endpoint and checks
    if the response is a list of flagged scrapes.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/scrapes/flagged")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_scrape_endpoint():
    """
    Test the scrape endpoint that triggers a scrape for a given URL.

    This test creates a URL, then calls the scrape endpoint for that URL,
    and checks if the response indicates a successful scrape.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First, create a URL
        url_response = await ac.post(
            "/urls/",
            json={
                "url": "https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-21H2"
            },
        )
        url_id = url_response.json()["id"]

        # Now, trigger a scrape for this URL
        response = await ac.post(f"/scrape/{url_id}")

    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_get_latest_endpoint():
    """
    Test the get_latest endpoint that retrieves the latest scrape for a URL.

    This test creates a URL and a scrape, then calls the get_latest endpoint
    for that URL, and checks if the response contains the correct scrape data.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First, create a URL and a scrape
        url_response = await ac.post(
            "/urls/",
            json={
                "url": "https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-21H2"
            },
        )
        url_id = url_response.json()["id"]
        scrape_response = await ac.post(
            "/scrapes/",
            json={"url_id": url_id, "data": {"key": "value"}, "create_alert": False},
        )

        # Now, get the latest scrape for this URL
        response = await ac.get(f"/latest/{url_id}")

    assert response.status_code == 200
    assert response.json()["url_id"] == url_id
    assert "data" in response.json()
