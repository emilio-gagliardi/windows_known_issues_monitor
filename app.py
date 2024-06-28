import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

API_URL = "http://localhost:8000"

st.set_page_config(layout="wide")


def fetch_urls():
    response = requests.get(f"{API_URL}/urls/")
    return response.json() if response.status_code == 200 else []


def fetch_scrapes(url_id, flagged=None):
    params = {}
    if flagged is not None:
        params["flagged"] = str(flagged).lower()
    response = requests.get(f"{API_URL}/scrapes/{url_id}", params=params)
    return response.json() if response.status_code == 200 else []


def fetch_all_flagged_scrapes():
    response = requests.get(f"{API_URL}/flagged_scrapes/")
    return response.json() if response.status_code == 200 else []


def update_scrape(scrape_id, scrape_type, scrape_comment, create_alert):
    data = {
        "scrape_type": scrape_type,
        "scrape_comment": scrape_comment,
        "create_alert": create_alert,
    }
    response = requests.put(f"{API_URL}/scrapes/{scrape_id}", json=data)
    return response.json() if response.status_code == 200 else None


def truncate_text(text, max_length=100):
    return text[:max_length] + "..." if len(text) > max_length else text


st.sidebar.title("Web Scraping Monitor")
page = st.sidebar.radio("Navigation", ["Dashboard", "Alerts"])

if page == "Dashboard":
    st.title("Scraping Dashboard")

    urls = fetch_urls()
    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]

    for i, url in enumerate(urls):
        with columns[i % 3]:
            st.header(url["url"])
            scrapes = fetch_scrapes(url["id"])

            for scrape in scrapes:
                with st.expander(
                    f"Scrape {scrape['id']} - {scrape['timestamp']}", expanded=False
                ):
                    full_content = scrape["content"]
                    truncated_content = truncate_text(full_content)

                    content_placeholder = st.empty()
                    content_placeholder.text_area(
                        "Content",
                        value=truncated_content,
                        height=100,
                        key=f"content_{scrape['id']}",
                    )

                    # Hover effect (note: this is a workaround as Streamlit doesn't support true hover effects)
                    if st.checkbox(
                        "Show full content", key=f"show_full_{scrape['id']}"
                    ):
                        content_placeholder.text_area(
                            "Content",
                            value=full_content,
                            height=200,
                            key=f"full_content_{scrape['id']}",
                        )

                    scrape_type = st.selectbox(
                        "Scrape Type",
                        options=["Critical", "Active", "Resolved", "Ignore"],
                        key=f"type_{scrape['id']}",
                        index=(
                            ["Critical", "Active", "Resolved", "Ignore"].index(
                                scrape["scrape_type"]
                            )
                            if scrape["scrape_type"]
                            else 0
                        ),
                    )

                    create_alert = st.checkbox(
                        "Create Alert",
                        key=f"alert_{scrape['id']}",
                        value=scrape["create_alert"],
                    )

                    scrape_comment = st.text_area(
                        "Comment",
                        value=scrape["scrape_comment"] or "",
                        key=f"comment_{scrape['id']}",
                    )

                    if st.button("Update", key=f"update_{scrape['id']}"):
                        updated_scrape = update_scrape(
                            scrape["id"], scrape_type, scrape_comment, create_alert
                        )
                        if updated_scrape:
                            st.success("Scrape updated successfully!")
                        else:
                            st.error("Failed to update scrape.")

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
