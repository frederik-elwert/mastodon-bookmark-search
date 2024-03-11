#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import sys

import bookmark_search
import polars as pl
import streamlit as st


@st.cache_data
def read_bookmarks():
    data = bookmark_search.read_bookmarks()
    docs = data.get_column("text").to_list()
    return data, docs


@st.cache_resource
def load_model(model="all-MiniLM-L6-v2"):
    from sentence_transformers import SentenceTransformer

    sentence_model = SentenceTransformer(model)
    return sentence_model


@st.cache_data
def compute_embeddings(_model, docs):
    return _model.encode(docs, show_progress_bar=False)


@st.cache_data
def compute_topics(docs, *, embeddings, _embedding_model):
    from bertopic import BERTopic
    from bertopic.representation import KeyBERTInspired

    representation_model = KeyBERTInspired()
    topic_model = BERTopic(
        embedding_model=_embedding_model, representation_model=representation_model
    )
    topic_model.fit(docs, embeddings=embeddings)
    return topic_model


def main():
    # Site title
    st.title("Mastodon Bookmark Search")
    # Get data
    data, docs = read_bookmarks()
    # Run topic model
    embedding_model = load_model()
    embeddings = compute_embeddings(embedding_model, docs)
    topic_model = compute_topics(
        docs, embeddings=embeddings, _embedding_model=embedding_model
    )
    topic_info = pl.from_pandas(topic_model.get_topic_info())
    # Add topic info to data
    new_topics = topic_model.reduce_outliers(docs, topic_model.topics_)
    data = data.with_columns(pl.Series(name="topic", values=new_topics))
    # Configure sidebar
    with st.sidebar:
        search_text = st.text_input("Search")
        hashtags = bookmark_search.get_hashtags(data)
        tag_options = hashtags.filter(pl.col("count") > 1).get_column("hashtags")
        selected_tags = st.multiselect("Hashtags", options=tag_options)
        topic_options = topic_info.get_column("Name")
        selected_topic = st.selectbox("Topic", options=topic_options, index=None)
    # Filter data
    for tag in selected_tags:
        data = data.filter(pl.col("hashtags").list.contains(tag))
    if selected_topic:
        topic_id = (
            # fmt:off
            topic_info
            .filter(pl.col("Name") == selected_topic)
            .select("Topic")
            .item()
        )
        print(selected_topic, topic_id)
        data = data.filter(pl.col("topic") == topic_id)
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
