import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import re
from urllib.parse import urlparse
import logging
from operator import itemgetter
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(layout="wide")


def fetch_urls():
    response = requests.get(f"{API_URL}/urls/")
    if response.status_code == 200:
        urls = response.json()
        # Sort the list of dictionaries based on the 'url' key
        sorted_urls = sorted(urls, key=itemgetter("url"))
        logger.info(f"\nfetch_urls finds (sorted): {sorted_urls}\n")
        return sorted_urls
    else:
        logger.error(f"Error fetching URLs: {response.status_code}")
        return []


def parse_date(date_string):
    try:
        # Remove the "PT" timezone indicator and parse the date
        date_string = date_string.replace(" PT", "")
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M")
    except ValueError:
        print(f"Warning: Unable to parse date '{date_string}'.")
        return None


def fetch_scrapes(url_id, flagged=None, limit=2):
    params = {"limit": limit}
    if flagged is not None:
        params["flagged"] = str(flagged).lower()

    full_url = f"{API_URL}/scrapes/urlid/{url_id}"
    print(f"Fetching scrapes from: {full_url} with params: {params}")
    response = requests.get(full_url, params=params)
    print(f"Response status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Number of scrapes received: {len(data)}")
        return data[:limit]  # Return only the top 'limit' number of scrapes
    else:
        print(f"Error fetching scrapes: {response.status_code}")
        return []


def fetch_all_flagged_scrapes():
    response = requests.get(f"{API_URL}/flagged_scrapes/")
    return response.json() if response.status_code == 200 else []


def process_url_for_title(url):
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


def update_scrape(scrape_id, scrape_type, scrape_comment, create_alert):
    data = {
        "scrape_type": scrape_type,
        "scrape_comment": scrape_comment,
        "create_alert": create_alert,
    }
    response = requests.put(f"{API_URL}/scrapes/{scrape_id}", json=data)
    return response.json() if response.status_code == 200 else None


def truncate_text(text, max_length=100):
    return text[: max_length - 3] + "..." if len(text) > max_length else text


def pad_text(text, pad_length=300):
    if len(text) >= pad_length:
        return text[:pad_length]
    else:
        return text + " " + "." * (pad_length - len(text))


def create_alert(scrape_id):
    # Placeholder function for creating an alert
    logger.info(f"Creating the alert for scrape_id: {scrape_id}")
    pass


st.sidebar.title("Web Scraping Monitor")
page = st.sidebar.radio("Navigation", ["Dashboard", "Alerts"])

if page == "Dashboard":
    st.title("Scraping Dashboard")

    urls = fetch_urls()
    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]

    for i, url in enumerate(urls):
        with columns[i % 3]:
            processed_title = process_url_for_title(url["url"])
            st.subheader(processed_title)
            scrapes = fetch_scrapes(url["id"])[:3]  # Limit to 3 most recent scrapes
            if not scrapes:
                st.warning(f"No scrapes found for URL: {url['url']}")
            else:
                for scrape in scrapes:
                    content_json = json.loads(scrape["content"])
                    known_issues = content_json["known_issues"]
                    row = known_issues["row"]
                    if len(row["Summary"]) > 300:
                        summary = truncate_text(row["Summary"], 300)
                    else:
                        summary = pad_text(row["Summary"], 300)
                    # Closed state view
                    closed_state_view = (
                        f"{row['Last updated']} - {len(summary)} - {summary}"
                    )

                    with st.expander(closed_state_view, expanded=False):
                        # Open state view with formatted content
                        st.markdown(
                            f"**Known Issue**\n"
                            f"Last updated: {row['Last updated']}\n\n"
                            f"{row['Summary']}"
                        )
                        detail_url = f"{url['url']}#issue-details"
                        st.markdown(
                            f"[View Details]({detail_url})", unsafe_allow_html=True
                        )
                        # Checkbox 1: Create Alert
                        create_alert_checked = st.checkbox(
                            "Create alert", key=f"create_alert_{scrape['id']}"
                        )

                        # Checkbox 2: Add Feedback
                        add_feedback_checked = st.checkbox(
                            "Add Feedback", key=f"add_feedback_{scrape['id']}"
                        )

                        if add_feedback_checked:
                            # Dropdown for Scrape Type
                            scrape_type = st.selectbox(
                                "Scrape Type",
                                ["Critical", "Active", "Resolved", "Unknown"],
                                key=f"scrape_type_{scrape['id']}",
                            )

                            # Textarea for Comment
                            scrape_comment = st.text_area(
                                "Comment", key=f"scrape_comment_{scrape['id']}"
                            )

                            # Update button
                            if st.button("Update", key=f"update_{scrape['id']}"):
                                update_scrape(
                                    scrape["id"],
                                    scrape_type,
                                    scrape_comment,
                                    create_alert_checked,
                                )
                                st.success("Scrape updated successfully!")

            if st.button("Export JSON", key=f"export_{url['id']}"):
                json_data = json.dumps(scrapes, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"scrapes_{url['id']}.json",
                    mime="application/json",
                )

elif page == "Alerts":
    st.title("Alerts")
    all_alerts = fetch_all_flagged_scrapes()

    if all_alerts:
        alert_df = pd.DataFrame(all_alerts)
        alert_df = alert_df[
            ["id", "url_id", "timestamp", "scrape_type", "scrape_comment"]
        ]

        # Fetch URL information to display URL instead of url_id
        urls = fetch_urls()
        url_dict = {url["id"]: url["url"] for url in urls}
        alert_df["url"] = alert_df["url_id"].map(url_dict)
        alert_df = alert_df.drop("url_id", axis=1)

        st.dataframe(alert_df)
    else:
        st.info("No alerts set.")

# Add new URL
st.sidebar.header("Add New URL")
new_url = st.sidebar.text_input("Enter new URL")
if st.sidebar.button("Add URL"):
    response = requests.post(f"{API_URL}/urls/", json={"url": new_url})
    if response.status_code == 200:
        st.sidebar.success("URL added successfully!")
    else:
        st.sidebar.error("Failed to add URL.")

# Trigger manual scrape
st.sidebar.header("Trigger Manual Scrape")
if st.sidebar.button("Scrape Now"):
    st.sidebar.info("Scraping initiated. This feature is not yet implemented.")
