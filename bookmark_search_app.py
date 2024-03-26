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


@st.cache_data
def generate_topic_map(_topic_model, *, docs, embeddings):
    return _topic_model.visualize_documents(docs=docs, embeddings=embeddings)


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
    topics = topic_model.topics_
    new_topics = topic_model.reduce_outliers(docs, topics)
    data = data.with_columns(
        pl.Series(name="topic", values=topics),
        pl.Series(name="new_topic", values=new_topics),
    )
    # Configure sidebar
    with st.sidebar:
        search_text = st.text_input("Search")
        use_semantic_search = st.toggle("Use semantic search")
        hashtags = bookmark_search.get_hashtags(data)
        tag_options = hashtags.filter(pl.col("count") > 1).get_column("hashtags")
        selected_tags = st.multiselect("Hashtags", options=tag_options)
        topic_options = topic_info.get_column("Name")
        selected_topic = st.selectbox("Topic", options=topic_options, index=None)
        reduce_outliers = st.toggle("Reduce outliers")
        show_topic_map = st.toggle("Show topic map")
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
        if reduce_outliers:
            data = data.filter(pl.col("new_topic") == topic_id)
        else:
            data = data.filter(pl.col("topic") == topic_id)
    if search_text:
        if use_semantic_search:
            from sentence_transformers import util

            query_embedding = embedding_model.encode(
                search_text, convert_to_tensor=True
            )
            n_results = 20
            hits = util.semantic_search(query_embedding, embeddings, top_k=n_results)
            hits_df = pl.DataFrame(hits[0], schema_overrides={"corpus_id": pl.UInt32})
            data = (
                data.with_row_index()
                .join(hits_df, left_on="index", right_on="corpus_id")
                .sort("score", descending=True)
            )
        else:
            data = data.filter(
                pl.col("text").str.to_lowercase().str.contains(search_text.lower())
            )
    # Display topic map
    if show_topic_map:
        topic_map = generate_topic_map(topic_model, docs=docs, embeddings=embeddings)
        st.plotly_chart(topic_map)
    # Display results
    for row in data.iter_rows(named=True):
        text = row["text"]
        if search_text:
            text = text.replace(search_text, f":orange[{search_text}]")
        st.markdown(
            f"""
**{row["user_display_name"]}** :gray[@{row["user_acct"].replace("@", "​@")}]

{text}
"""
        )
        st.caption(f"""[{row["created_at"]}]({row["url"]})""")
        st.divider()


if __name__ == "__main__":
    main()
