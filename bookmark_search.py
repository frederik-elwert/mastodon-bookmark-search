#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import sys
from pathlib import Path
import html

import bleach
import polars as pl

BOOKMARK_FILE = Path("bookmarks.json")


def read_bookmarks():
    data = pl.read_ndjson(BOOKMARK_FILE, ignore_errors=True)
    data = data.select(
        "id",
        "created_at",
        "language",
        "url",
        "content",
        pl.col("content")
        .str.replace_all(r"<br>", "\n")
        .map_elements(lambda s: html.unescape(bleach.clean(s, tags={}, strip=True)))
        .alias("text"),
        "replies_count",
        "reblogs_count",
        "favourites_count",
        pl.col("account").struct.field("acct").alias("user_acct"),
        pl.col("account").struct.field("display_name").alias("user_display_name"),
        pl.col("tags")
        .list.eval(pl.element().struct.field("name").str.to_lowercase())
        .alias("hashtags"),
    )
    return data


def get_hashtags(data):
    return (
        data.get_column("hashtags").list.explode().drop_nulls().value_counts(sort=True)
    )


def main():
    # Parse commandline arguments
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-v", "--verbose", action="store_true")
    arg_parser.add_argument(
        "-o", "--outfile", default=sys.stdout, type=argparse.FileType("w")
    )
    args = arg_parser.parse_args()
    # Set up logging
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.ERROR
    logging.basicConfig(level=level)
    # Return exit value
    data = read_bookmarks()
    hashtags = get_hashtags(data)
    print(hashtags)
    return 0


if __name__ == "__main__":
    sys.exit(main())
