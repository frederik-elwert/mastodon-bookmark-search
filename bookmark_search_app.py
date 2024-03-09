#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import sys

import bookmark_search
import polars as pl
import streamlit as st

read_bookmarks = st.cache_data(bookmark_search.read_bookmarks)


def main():
    # Site title
    st.title("Mastodon Bookmark Search")
    # Get data
    data = read_bookmarks()
    # Configure sidebar
    with st.sidebar:
        search_text = st.text_input("Search")
        hashtags = bookmark_search.get_hashtags(data)
        tag_options = hashtags.filter(pl.col("count") > 1).get_column("hashtags")
        selected_tags = st.multiselect("Hashtags", options=tag_options)
    # Filter data
    for tag in selected_tags:
        data = data.filter(pl.col("hashtags").list.contains(tag))
    if search_text:
        data = data.filter(pl.col("text").str.contains(search_text))
    # Display results
    for row in data.iter_rows(named=True):
        st.markdown(
            f"""
**{row["user_display_name"]}** :gray[@{row["user_acct"].replace("@", "​@")}]

{row["text"]}
"""
        )
        st.caption(f"""[{row["created_at"]}]({row["url"]})""")
        st.divider()


if __name__ == "__main__":
    main()
