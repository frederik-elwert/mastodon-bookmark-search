import json
from pathlib import Path
import shutil
import argparse
import getpass

from mastodon import Mastodon

BOOKMARK_FILE = Path("bookmarks.json")
BOOKMARK_FILE_TMP = Path("bookmarks.json.tmp")

CLIENT_SECRETS_FILE = "mbs_client.secret"
USER_SECRETS_FILE = "mbs_user.secret"


def register_app(base_url, client_cred_file):
    Mastodon.create_app(
        "mastodon-bookmark-search",
        api_base_url=base_url,
        to_file=client_cred_file,
    )
    print(f"Application registered. Client credentials saved to {client_cred_file}")


def login(base_url, client_cred_file, user_cred_file, email, password):
    mastodon = Mastodon(client_id=client_cred_file, api_base_url=base_url)
    mastodon.log_in(email, password, to_file=user_cred_file)
    print(f"User logged in. User credentials saved to {user_cred_file}")


def ingest():
    if not Path(USER_SECRETS_FILE).is_file():
        print(
            f'No credentials. Log in first using "python {Path(__file__).name} login".'
        )
        return
    mastodon = Mastodon(access_token=USER_SECRETS_FILE)
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


def main():
    parser = argparse.ArgumentParser(description="Mastodon CLI Application")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Sub-command: login
    login_parser = subparsers.add_parser(
        "login", help="Register and log in to Mastodon"
    )
    login_parser.add_argument(
        "--client-cred-file",
        type=str,
        default=CLIENT_SECRETS_FILE,
        help="File to save client credentials",
    )
    login_parser.add_argument(
        "--user-cred-file",
        type=str,
        default=USER_SECRETS_FILE,
        help="File to save user credentials",
    )

    # Sub-command: ingest
    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest bookmarks from Mastodon into the search app"
    )

    args = parser.parse_args()

    if args.command == "login":
        try:
            base_url = input("Enter the base URL of the Mastodon instance: ")
            email = input("Enter your email address: ")
            password = getpass.getpass("Enter your password: ")
        except KeyboardInterrupt:
            print("\nAborting")
            return

        register_app(base_url, args.client_cred_file)
        login(base_url, args.client_cred_file, args.user_cred_file, email, password)
    elif args.command == "ingest":
        ingest()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
