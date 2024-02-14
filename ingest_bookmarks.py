import json
from pathlib import Path
import shutil

from mastodon import Mastodon

BOOKMARK_FILE = Path("bookmarks.json")
BOOKMARK_FILE_TMP = Path("bookmarks.json.tmp")

mastodon = Mastodon(access_token="mbs_user.secret")

# Get last saved bookmark
last_bookmark_id = None
if BOOKMARK_FILE.is_file():
    with BOOKMARK_FILE.open() as infile:
        for line in infile:
            break
        bookmark = json.loads(line)
        last_bookmark_id = bookmark["id"]

# Get new bookmarks
bookmarks = mastodon.bookmarks()
with BOOKMARK_FILE_TMP.open("w") as outfile:
    while bookmarks:
        for bookmark in bookmarks:
            # We already have that bookmark, end here.
            if bookmark["id"] == last_bookmark_id:
                break
            outfile.write(json.dumps(bookmark, default=str))
            outfile.write("\n")
        # Python weirdness: for/else gets executed when no
        # break statement is encountered. Used here to control
        # the outer while loop.
        else:
            print("Get next page")
            bookmarks = mastodon.fetch_next(bookmarks)
            continue
        break

if BOOKMARK_FILE.is_file():
    # Merge the new and old bookmarks files
    with BOOKMARK_FILE_TMP.open("a") as outfile, BOOKMARK_FILE.open() as infile:
        shutil.copyfileobj(infile, outfile)
BOOKMARK_FILE_TMP.rename(BOOKMARK_FILE)
