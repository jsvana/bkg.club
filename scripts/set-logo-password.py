#!/usr/bin/env python3
"""Set (or rotate) the passphrase on the Badge Forge page, logo.html.

The passphrase itself is never stored anywhere in this repo. What gets written
into logo.html is a random salt plus the PBKDF2-SHA256 hash of the passphrase,
between the /* GATE:START */ and /* GATE:END */ markers.

Usage:
    python3 scripts/set-logo-password.py            # prompts twice, hidden input
    BKG_LOGO_PASSWORD='...' python3 scripts/set-logo-password.py   # non-interactive

Then commit logo.html and push. The new passphrase is live on the next deploy.

WHAT THIS DOES AND DOESN'T BUY YOU
----------------------------------
bkg.club is a static site in a PUBLIC repo. There is no server to check a
password against, so the check runs in the visitor's browser and the hash is
readable by anyone. That means:

  * It DOES keep drive-by visitors and search engines out of the forge.
  * It DOES avoid storing the passphrase in plaintext anywhere.
  * It does NOT stop someone who is willing to run a wordlist against the
    hash offline. Pick a passphrase that isn't in a wordlist.
  * It is NOT suitable for guarding anything that costs money or leaks data.
    The forge is safe behind it precisely because it holds neither: it's pure
    client-side drawing, with no API key and no per-use cost.

If we ever put a paid image API behind this page, the password check has to
move to a server that holds the key. See docs/LOGO-GENERATOR.md.
"""

import base64
import getpass
import hashlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = REPO_ROOT / "logo.html"

START_MARKER = "/* GATE:START */"
END_MARKER = "/* GATE:END */"

ITERATIONS = 250_000
SALT_BYTES = 16
KEY_BYTES = 32
MIN_LENGTH = 10


def derive(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, ITERATIONS, KEY_BYTES)


def read_passphrase() -> str:
    from_env = os.environ.get("BKG_LOGO_PASSWORD")
    if from_env:
        return from_env

    if not sys.stdin.isatty():
        sys.exit("ERROR: no TTY for a prompt. Set BKG_LOGO_PASSWORD instead.")

    first = getpass.getpass("New Badge Forge passphrase: ")
    second = getpass.getpass("Again, to be sure: ")
    if first != second:
        sys.exit("ERROR: those didn't match. Nothing changed.")
    return first


def render_block(salt: bytes, digest: bytes) -> str:
    return (
        f"    {START_MARKER}\n"
        "    const GATE = {\n"
        f'        salt: "{base64.b64encode(salt).decode()}",\n'
        f"        iterations: {ITERATIONS},\n"
        f'        hash: "{base64.b64encode(digest).decode()}"\n'
        "    };\n"
        f"    {END_MARKER}"
    )


def main() -> int:
    if not LOGO_PATH.is_file():
        sys.exit(f"ERROR: {LOGO_PATH} not found.")

    html = LOGO_PATH.read_text()
    start = html.find(START_MARKER)
    end = html.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        sys.exit(f"ERROR: couldn't find the {START_MARKER} / {END_MARKER} block in {LOGO_PATH.name}.")

    passphrase = read_passphrase()
    if len(passphrase) < MIN_LENGTH:
        sys.exit(
            f"ERROR: use at least {MIN_LENGTH} characters. The hash ships to every "
            "visitor, so a short passphrase is a guessable one."
        )

    salt = os.urandom(SALT_BYTES)
    digest = derive(passphrase, salt)

    # Replace from the start of the START_MARKER line through the END_MARKER.
    line_start = html.rfind("\n", 0, start) + 1
    updated = html[:line_start] + render_block(salt, digest) + html[end + len(END_MARKER):]
    LOGO_PATH.write_text(updated)

    print(f"Updated the passphrase gate in {LOGO_PATH.name}.")
    print(f"  PBKDF2-SHA256, {ITERATIONS:,} iterations, {SALT_BYTES}-byte random salt")
    print("Commit logo.html and push to put it live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
