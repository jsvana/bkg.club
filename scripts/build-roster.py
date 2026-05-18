#!/usr/bin/env python3
"""Fetch the BKG roster CSV from Google Sheets and render it into index.html + members.txt.

The roster section of index.html is rebuilt between <!-- ROSTER:START --> and
<!-- ROSTER:END --> markers. The members count is updated between
<!-- MEMBER_COUNT:START --> and <!-- MEMBER_COUNT:END -->. members.txt is a
Ham2K PoLo callsign notes file (auto-generated, not manually edited).
"""

import csv
import io
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SHEET_ID = "1GPNjke3fDf18amh3KbUpUAJUqMu4nOuFLm1F8CDzbrY"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "index.html"
MEMBERS_TXT_PATH = REPO_ROOT / "members.txt"
MUGSHOT_DIR = REPO_ROOT / "images" / "mugshots"
MUGSHOT_REL_DIR = "images/mugshots"
MUGSHOT_OVERRIDE_DIR = REPO_ROOT / "images" / "mugshots-override"
MUGSHOT_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

NEW_BADGE_LIMIT = 3  # last N members get the "NEW!!" badge
OG_BADGE_NUMBERS = {2}  # member numbers that get the "OG" badge (founder #1 has its own treatment)

QRZ_XML_URL = "https://xmldata.qrz.com/xml/current/"
QRZ_NS = {"q": "http://xmldata.qrz.com"}


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fetch_csv() -> str:
    req = urllib.request.Request(
        SHEET_CSV_URL,
        headers={"User-Agent": "BKG-Roster-Builder/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_member_number(raw: str) -> int:
    """Extract integer from values like 'BKG1', 'BKG #1', '1'."""
    match = re.search(r"\d+", raw or "")
    return int(match.group(0)) if match else 0


def parse_members(csv_text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(csv_text))
    members = []
    for row in reader:
        callsign = (row.get("Callsign") or "").strip()
        name = (row.get("Name") or "").strip()
        join_date = (row.get("Join Date") or "").strip()
        number = parse_member_number(row.get("#") or row.get("BKG #") or "")
        if callsign and number:
            members.append(
                {
                    "callsign": callsign,
                    "name": name,
                    "join_date": join_date,
                    "number": number,
                }
            )
    members.sort(key=lambda m: m["number"])
    return members


def _qrz_get_raw(params: dict[str, str]) -> bytes | None:
    url = QRZ_XML_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "BKG-Roster-Builder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"  QRZ request failed: {exc}", file=sys.stderr)
        return None


def _qrz_get(params: dict[str, str]) -> ET.Element | None:
    raw = _qrz_get_raw(params)
    if raw is None:
        return None
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        print(f"  QRZ XML parse failed: {exc}", file=sys.stderr)
        return None


def qrz_login(username: str, password: str) -> str | None:
    """Authenticate with QRZ XML API; returns a session key or None."""
    root = _qrz_get({"username": username, "password": password, "agent": "bkg.club-1.0"})
    if root is None:
        return None
    session = root.find("q:Session", QRZ_NS)
    if session is None:
        return None
    error = session.find("q:Error", QRZ_NS)
    if error is not None and error.text:
        print(f"  QRZ login error: {error.text}", file=sys.stderr)
        return None
    key = session.find("q:Key", QRZ_NS)
    return key.text if key is not None and key.text else None


def qrz_fetch_callsign(session_key: str, callsign: str, *, debug: bool = False) -> dict:
    """Look up a callsign. Returns {'state': str|None, 'image': str|None}."""
    empty = {"state": None, "image": None}
    raw = _qrz_get_raw({"s": session_key, "callsign": callsign})
    if raw is None:
        return empty
    if debug:
        print(f"  QRZ response for {callsign}:", file=sys.stderr)
        for line in raw.decode("utf-8", errors="replace").splitlines():
            print(f"    {line}", file=sys.stderr)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        print(f"  QRZ parse error for {callsign}: {exc}", file=sys.stderr)
        return empty
    # Surface session-level errors (e.g. "Session Timeout", "Not subscribed").
    session = root.find("q:Session", QRZ_NS)
    if session is not None:
        err = session.find("q:Error", QRZ_NS)
        if err is not None and err.text:
            print(f"  QRZ session error for {callsign}: {err.text}", file=sys.stderr)
    call = root.find("q:Callsign", QRZ_NS)
    if call is None:
        return empty

    state = None
    state_elem = call.find("q:state", QRZ_NS)
    if state_elem is not None and state_elem.text:
        text = state_elem.text.strip().upper()
        if re.fullmatch(r"[A-Z]{2}", text):
            state = text

    image = None
    image_elem = call.find("q:image", QRZ_NS)
    if image_elem is not None and image_elem.text:
        candidate = image_elem.text.strip()
        if candidate.startswith(("http://", "https://")):
            image = candidate

    return {"state": state, "image": image}


def local_override_mugshot(callsign: str) -> str | None:
    """If images/mugshots-override/<callsign>.<ext> exists, copy it into the build
    mugshot dir and return its repo-relative path. Otherwise return None."""
    if not MUGSHOT_OVERRIDE_DIR.is_dir():
        return None
    for ext in MUGSHOT_EXTS:
        src = MUGSHOT_OVERRIDE_DIR / f"{callsign}{ext}"
        if src.is_file():
            MUGSHOT_DIR.mkdir(parents=True, exist_ok=True)
            dest = MUGSHOT_DIR / f"{callsign}{ext}"
            dest.write_bytes(src.read_bytes())
            return f"{MUGSHOT_REL_DIR}/{callsign}{ext}"
    return None


def download_mugshot(callsign: str, url: str) -> str | None:
    """Download a QRZ profile image. Returns the repo-relative path, or None on failure."""
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in MUGSHOT_EXTS:
        suffix = ".jpg"
    MUGSHOT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{callsign}{suffix}"
    dest = MUGSHOT_DIR / filename
    req = urllib.request.Request(url, headers={"User-Agent": "BKG-Roster-Builder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"  QRZ image download failed for {callsign}: {exc}", file=sys.stderr)
        return None
    if not data:
        return None
    dest.write_bytes(data)
    return f"{MUGSHOT_REL_DIR}/{filename}"


def annotate_qrz(members: list[dict]) -> None:
    """Set member['state'], member['state_og'], and member['mugshot_path'] in place.

    Requires env vars QRZ_USERNAME and QRZ_PASSWORD (an XML-subscription QRZ
    account). Raises RuntimeError if creds are missing or login fails.
    """
    for member in members:
        member["state"] = None
        member["state_og"] = False
        member["mugshot_path"] = None

    username = os.environ.get("QRZ_USERNAME")
    password = os.environ.get("QRZ_PASSWORD")
    if not username or not password:
        raise RuntimeError("QRZ_USERNAME and QRZ_PASSWORD must be set")

    session_key = qrz_login(username, password)
    if not session_key:
        raise RuntimeError("QRZ login failed")

    for idx, member in enumerate(members):
        info = qrz_fetch_callsign(session_key, member["callsign"], debug=(idx == 0))
        member["state"] = info["state"]
        override = local_override_mugshot(member["callsign"])
        if override:
            member["mugshot_path"] = override
        elif info["image"]:
            member["mugshot_path"] = download_mugshot(member["callsign"], info["image"])
    resolved = sum(1 for m in members if m.get("state"))
    mugshots = sum(1 for m in members if m.get("mugshot_path"))
    print(f"  QRZ resolved state for {resolved}/{len(members)} members", file=sys.stderr)
    print(f"  Mugshot resolved for {mugshots}/{len(members)} members (local overrides preferred)", file=sys.stderr)

    earliest: dict[str, dict] = {}
    for member in sorted(members, key=lambda m: m["number"]):
        state = member.get("state")
        if state and state not in earliest:
            earliest[state] = member
    for member in earliest.values():
        member["state_og"] = True


def first_name_initial(name: str) -> str:
    """Return 'First L' from 'First Last' (handles suffixes like 'Jr')."""
    if not name:
        return ""
    parts = [p.strip(",") for p in name.split() if p.strip(",")]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    first = parts[0]
    # skip suffixes when picking last initial
    suffixes = {"Jr", "Sr", "II", "III", "IV"}
    last_candidates = [p for p in parts[1:] if p.rstrip(".") not in suffixes]
    if not last_candidates:
        return first
    return f"{first} {last_candidates[-1][0].upper()}"


def state_og_badge_html(member: dict) -> str:
    if not member.get("state_og"):
        return ""
    state = html_escape(member.get("state") or "")
    return f'\n                    <div class="state-og-badge">{state} OG</div>'


def mugshot_inner_html(member: dict) -> str:
    path = member.get("mugshot_path")
    if path:
        callsign = html_escape(member["callsign"])
        src = html_escape(path)
        return (
            f'<img class="mugshot-photo" src="{src}" alt="{callsign} QRZ profile photo" loading="lazy">'
        )
    return (
        '<div class="mugshot-placeholder">\n'
        '                            <span class="icon">👤</span>\n'
        '                            MUGSHOT<br>PENDING\n'
        '                        </div>'
    )


def render_founder_card(member: dict) -> str:
    callsign = html_escape(member["callsign"])
    name = html_escape(member["name"])
    number = f"BKG #{member['number']:03d}"
    state_og_html = state_og_badge_html(member)
    mugshot_inner = mugshot_inner_html(member)
    return f"""                <!-- FOUNDER - {callsign} - THE OG BRASS POUNDER -->
                <div class="member-card founder-card">{state_og_html}
                    <div class="founder-badge">👑 GODFATHER 👑</div>
                    <div class="founder-flames"></div>
                    <div class="mugshot founder-mugshot">
                        {mugshot_inner}
                        <div class="founder-glow"></div>
                    </div>
                    <div class="member-info founder-info">
                        <a href="https://www.qrz.com/db/{callsign}" target="_blank" class="member-callsign founder-callsign">{callsign}</a>
                        <div class="founder-title">🤜 THE OG BRASS POUNDER 🤛</div>
                        <div class="member-number">{number}</div>
                        <div class="member-name">{name}</div>
                        <div class="founder-quote">"2m CW or DIE"</div>
                    </div>
                    <div class="founder-sparks"></div>
                </div>"""


def render_member_card(member: dict, *, is_og: bool, is_new: bool) -> str:
    callsign = html_escape(member["callsign"])
    name = html_escape(member["name"])
    number = f"BKG #{member['number']:03d}"
    badge_html = ""
    if is_og:
        badge_html = '\n                    <div class="og-badge">OG</div>'
    elif is_new:
        badge_html = '\n                    <div class="new-badge">NEW!!</div>'
    badge_html += state_og_badge_html(member)
    mugshot_inner = mugshot_inner_html(member)
    return f"""                <!-- {callsign} -->
                <div class="member-card">{badge_html}
                    <div class="mugshot">
                        {mugshot_inner}
                    </div>
                    <div class="member-info">
                        <a href="https://www.qrz.com/db/{callsign}" target="_blank" class="member-callsign">{callsign}</a>
                        <div class="member-number">{number}</div>
                        <div class="member-name">{name}</div>
                    </div>
                </div>"""


def render_ghost_card(next_number: int) -> str:
    number = f"BKG #{next_number:03d}"
    return f"""                <!-- Placeholder for future members -->
                <div class="member-card ghost">
                    <div class="mugshot">
                        <div class="mugshot-placeholder">
                            <span class="icon">❓</span>
                            UR CALL<br>HERE??
                        </div>
                    </div>
                    <div class="member-info">
                        <div class="member-callsign">??????</div>
                        <div class="member-number">{number}</div>
                        <div class="member-name">Could be U!!</div>
                    </div>
                </div>"""


def render_roster_block(members: list[dict]) -> str:
    if not members:
        return ""
    new_numbers = {m["number"] for m in members[-NEW_BADGE_LIMIT:]}
    cards: list[str] = []
    for member in members:
        if member["number"] == 1:
            cards.append(render_founder_card(member))
        else:
            cards.append(
                render_member_card(
                    member,
                    is_og=member["number"] in OG_BADGE_NUMBERS,
                    is_new=member["number"] in new_numbers,
                )
            )
    next_number = max(m["number"] for m in members) + 1
    cards.append(render_ghost_card(next_number))
    return "\n\n".join(cards)


def replace_between(html: str, start_marker: str, end_marker: str, replacement: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    if not pattern.search(html):
        raise RuntimeError(f"Markers not found: {start_marker} ... {end_marker}")
    return pattern.sub(start_marker + replacement + end_marker, html, count=1)


def update_index(members: list[dict]) -> None:
    html = INDEX_PATH.read_text()
    roster = render_roster_block(members)
    html = replace_between(
        html,
        "<!-- ROSTER:START - auto-generated by scripts/build-roster.py from Google Sheet -->",
        "<!-- ROSTER:END -->",
        "\n" + roster + "\n                ",
    )
    html = replace_between(
        html,
        "<!-- MEMBER_COUNT:START -->",
        "<!-- MEMBER_COUNT:END -->",
        str(len(members)),
    )
    html = replace_between(
        html,
        "<!-- BUILD_TIME:START -->",
        "<!-- BUILD_TIME:END -->",
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
    INDEX_PATH.write_text(html)


def render_members_txt(members: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# BKG Callsign Notes for Ham2K PoLo",
        f"# Generated: {now}",
        "# Do not edit manually - this file is auto-generated",
        "",
    ]
    for member in sorted(members, key=lambda m: m["callsign"]):
        label = first_name_initial(member["name"])
        lines.append(f"{member['callsign']} 🤜 {label} BKG #{member['number']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    print(f"Fetching roster from {SHEET_CSV_URL}")
    try:
        csv_text = fetch_csv()
    except Exception as exc:
        print(f"ERROR: Failed to fetch CSV: {exc}", file=sys.stderr)
        return 1

    members = parse_members(csv_text)
    if not members:
        print("ERROR: No members parsed from CSV", file=sys.stderr)
        return 1
    print(f"Parsed {len(members)} members (BKG #{members[0]['number']:03d}–#{members[-1]['number']:03d})")

    print("Looking up state + mugshot for each member via QRZ XML API")
    annotate_qrz(members)
    og_count = sum(1 for m in members if m.get("state_og"))
    print(f"Marked {og_count} state OG(s) across {len({m['state'] for m in members if m.get('state')})} state(s)")

    update_index(members)
    print(f"Updated {INDEX_PATH.name}")

    MEMBERS_TXT_PATH.write_text(render_members_txt(members))
    print(f"Wrote {MEMBERS_TXT_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
