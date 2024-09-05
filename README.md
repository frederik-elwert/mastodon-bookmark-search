# Mastodon Bookmark Search

A simple web application based on Streamlit that allows you to search and explore your Mastodon bookmarks.

## Usage

1. To install the dependencies, run

    ```bash
    pipenv install
    ```

Currently, the dependencies are locked for Python 3.10 on Linux. If you are on a different version or platform and pipenv fails, try deleting the virtual environment (with `pipenv --rm`), delete (or rename) _`Pipfile.lock`_, and then run `pipenv install` again.

2. Set up credentials for your Mastodon server with

    ```bash
    pipenv run python ingest_bookmarks.py login
    ```

3. Import your bookmarks with

    ```bash
    pipenv run python ingest_bookmarks.py ingest
    ```

4. Run the web app with

    ```bash
    pipenv run streamlit run bookmark_search_app.py
    ```
