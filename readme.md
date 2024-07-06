# Web Scraper Application

This project is a web scraping application that periodically scrapes specified URLs for data, stores the results in a PostgreSQL database, and provides a Streamlit-based web interface to interact with the scraped data.

## Features

- **Asynchronous Web Scraping:** Utilizes asynchronous tasks to scrape data from URLs.
- **Database Integration:** Stores scraped data in a PostgreSQL database.
- **Streamlit Web Interface:** Provides a user-friendly web interface to view and manage scraped data.
- **Scheduler:** Periodically scrapes URLs at a specified time daily.

## Prerequisites

- Python 3.8+
- PostgreSQL
- Environment variables set up in a `.env` file:

## Running the Application

1. **Start the FastAPI server:**
    ```sh
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```

2. **Start the Streamlit app:**
    ```sh
    streamlit run app/app.py
    ```

3. **Access the Streamlit web interface:**
    Open your browser and navigate to `http://localhost:8501` to view the web interface.

## PostgreSQL Database

The application uses PostgreSQL to store scraped data. Ensure that your PostgreSQL server is running and the database is properly configured with the credentials specified in the `.env` file.

## Contributing

Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.

---

`Source: app\main.py`
`Source: app\database.py`
`Source: app\initial_setup.py`
`Source: app\app.py`