# Mastodon Bookmark Search

A simple web application based on Streamlit that allows you to search and explore your Mastodon bookmarks.

## Usage

1. To install the dependencies, run

    ```bash
    pipenv install
    ```

2. Set up credentials for your Mastodon server following the example for [Mastodon.py](https://github.com/halcy/Mastodon.py).

3. Import your bookmarks with

    ```bash
    pipenv run python ingest_bookmarks.py
    ```

4. Run the web app with

    ```bash
    pipenv run streamlit run bookmark_search_app.py
    ```
