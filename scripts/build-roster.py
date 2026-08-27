#!/usr/bin/env python3
"""Fetch the BKG roster CSV from Google Sheets and render it into index.html + members.txt.

The roster section of index.html is rebuilt between <!-- ROSTER:START --> and
<!-- ROSTER:END --> markers. The members count is updated between
<!-- MEMBER_COUNT:START --> and <!-- MEMBER_COUNT:END -->. members.txt is a
Ham2K PoLo callsign notes file (auto-generated, not manually edited).
"""

import csv
import io
import json
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
TREE_PATH = REPO_ROOT / "tree.html"
MEMBERS_TXT_PATH = REPO_ROOT / "members.txt"
NAME_OVERRIDES_PATH = REPO_ROOT / "name-overrides.txt"
MUGSHOT_DIR = REPO_ROOT / "images" / "mugshots"
MUGSHOT_REL_DIR = "images/mugshots"
MUGSHOT_OVERRIDE_DIR = REPO_ROOT / "images" / "mugshots-override"
MUGSHOT_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

NEW_BADGE_LIMIT = 3  # last N members get the "NEW!!" badge
OG_BADGE_NUMBERS = {2}  # member numbers that get the "OG" badge (founder #1 has its own treatment)

QRZ_XML_URL = "https://xmldata.qrz.com/xml/current/"
QRZ_NS = {"q": "http://xmldata.qrz.com"}

# The 50 states + DC drawn in the index.html SVG map.
US_MAP_STATES = frozenset(
    """
    AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN
    MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA
    WV WI WY
    """.split()
)

# QRZ country values (DXCC-style entity names) that belong on the US map
# rather than in the international DX box. Compared lowercase.
US_DXCC_NAMES = {"united states", "united states of america", "usa", "alaska", "hawaii"}

# DXCC entity name (as QRZ reports it, lowercased) -> flag emoji for the DX box.
# Anything missing falls back to the 🌍 globe.
COUNTRY_FLAGS = {
    "canada": "🇨🇦", "mexico": "🇲🇽", "england": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "northern ireland": "🇬🇧", "ireland": "🇮🇪", "france": "🇫🇷",
    "fed. rep. of germany": "🇩🇪", "germany": "🇩🇪", "italy": "🇮🇹", "spain": "🇪🇸",
    "portugal": "🇵🇹", "netherlands": "🇳🇱", "belgium": "🇧🇪", "switzerland": "🇨🇭",
    "austria": "🇦🇹", "sweden": "🇸🇪", "norway": "🇳🇴", "denmark": "🇩🇰",
    "finland": "🇫🇮", "iceland": "🇮🇸", "poland": "🇵🇱", "czech republic": "🇨🇿",
    "slovak republic": "🇸🇰", "hungary": "🇭🇺", "romania": "🇷🇴", "bulgaria": "🇧🇬",
    "greece": "🇬🇷", "croatia": "🇭🇷", "slovenia": "🇸🇮", "ukraine": "🇺🇦",
    "european russia": "🇷🇺", "asiatic russia": "🇷🇺", "estonia": "🇪🇪",
    "latvia": "🇱🇻", "lithuania": "🇱🇹", "japan": "🇯🇵", "republic of korea": "🇰🇷",
    "south korea": "🇰🇷", "china": "🇨🇳", "taiwan": "🇹🇼", "hong kong": "🇭🇰",
    "philippines": "🇵🇭", "indonesia": "🇮🇩", "thailand": "🇹🇭", "vietnam": "🇻🇳",
    "india": "🇮🇳", "israel": "🇮🇱", "turkey": "🇹🇷", "united arab emirates": "🇦🇪",
    "south africa": "🇿🇦", "egypt": "🇪🇬", "kenya": "🇰🇪", "nigeria": "🇳🇬",
    "morocco": "🇲🇦", "australia": "🇦🇺", "new zealand": "🇳🇿", "brazil": "🇧🇷",
    "argentina": "🇦🇷", "chile": "🇨🇱", "colombia": "🇨🇴", "peru": "🇵🇪",
    "uruguay": "🇺🇾", "paraguay": "🇵🇾", "bolivia": "🇧🇴", "ecuador": "🇪🇨",
    "venezuela": "🇻🇪", "costa rica": "🇨🇷", "panama": "🇵🇦", "guatemala": "🇬🇹",
    "honduras": "🇭🇳", "nicaragua": "🇳🇮", "el salvador": "🇸🇻", "belize": "🇧🇿",
    "dominican republic": "🇩🇴", "cuba": "🇨🇺", "jamaica": "🇯🇲", "bahamas": "🇧🇸",
    "trinidad & tobago": "🇹🇹", "puerto rico": "🇵🇷", "us virgin islands": "🇻🇮",
    "guam": "🇬🇺",
}


def member_map_bucket(member: dict) -> tuple[str, str] | None:
    """Where a member lands on the territory map.

    Returns ("state", "UT") for members on the US map, ("dx", "Canada") for
    international members, or None when there's nothing to plot. QRZ reports
    Canadian provinces and other subdivisions in the same <state> field as US
    states, so a bare two-letter code is only trusted when the country agrees.
    """
    state = member.get("state")
    country = (member.get("country") or "").strip()
    is_us = not country or country.lower() in US_DXCC_NAMES
    if is_us and state in US_MAP_STATES:
        return ("state", state)
    if country and not is_us:
        return ("dx", country)
    return None


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


def _norm_header(name: str) -> str:
    """Lowercase a header and collapse punctuation/whitespace to single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


# Header names (normalized) that mean "who recruited this member". The roster
# sheet's column is expected to be "Sponsor"; these aliases keep the build
# working if it's titled differently.
SPONSOR_HEADER_ALIASES = {
    "sponsor", "sponsored by", "sponsor callsign", "sponsor call",
    "recruiter", "recruited by", "referred by", "brought in by",
    "elmer", "upline",
}


def find_sponsor_header(fieldnames: list[str] | None) -> str | None:
    """Pick the sponsor column from the CSV headers, tolerant of naming/case.

    Matches a known alias first, then any header mentioning sponsor/recruit/
    upline/elmer. Returns the original header string, or None if absent.
    """
    headers = [h for h in (fieldnames or []) if h]
    norm_to_orig = {_norm_header(h): h for h in headers}
    for alias in SPONSOR_HEADER_ALIASES:
        if alias in norm_to_orig:
            return norm_to_orig[alias]
    for h in headers:
        n = _norm_header(h)
        if any(kw in n for kw in ("sponsor", "recruit", "upline", "elmer")):
            return h
    return None


def parse_members(csv_text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(csv_text))
    fieldnames = reader.fieldnames
    sponsor_key = find_sponsor_header(fieldnames)
    # Surface the sheet schema so a missing/renamed sponsor column (or the CSV
    # export hitting the wrong tab) is obvious in the build log.
    print(f"  CSV columns: {fieldnames}", file=sys.stderr)
    print(f"  Sponsor column detected as: {sponsor_key!r}", file=sys.stderr)
    if sponsor_key is None:
        print(
            "  WARNING: no sponsor column found — the downline tree will be flat. "
            "Expected a 'Sponsor' column on the exported sheet tab.",
            file=sys.stderr,
        )
    members = []
    for row in reader:
        callsign = (row.get("Callsign") or "").strip()
        name = (row.get("Name") or "").strip()
        join_date = (row.get("Join Date") or "").strip()
        number = parse_member_number(row.get("#") or row.get("BKG #") or "")
        # "Sponsor" = who recruited this member, as a callsign or BKG number.
        # Resolved to the sponsoring member in resolve_sponsors().
        sponsor_raw = ((row.get(sponsor_key) if sponsor_key else "") or "").strip()
        if callsign and number:
            members.append(
                {
                    "callsign": callsign,
                    "name": name,
                    "join_date": join_date,
                    "number": number,
                    "sponsor_raw": sponsor_raw,
                    "sponsor_member": None,
                }
            )
    members.sort(key=lambda m: m["number"])
    return members


def load_name_overrides() -> dict[str, str]:
    """Load callsign -> display-name overrides from name-overrides.txt.

    This file is manually maintained (unlike members.txt) and lets anyone
    override the name a member is shown with — the roster sheet stays the
    source of truth, but the override wins. It's the text-name analogue of the
    images/mugshots-override/ directory. Format, one entry per line:

        CALLSIGN = Display Name

    Blank lines and lines starting with '#' are ignored. The separator may be
    '=' or ':'. Callsigns are matched case-insensitively. Returns a dict keyed
    by upper-cased callsign; empty if the file is absent.
    """
    if not NAME_OVERRIDES_PATH.is_file():
        return {}
    overrides: dict[str, str] = {}
    for lineno, raw_line in enumerate(NAME_OVERRIDES_PATH.read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"([A-Za-z0-9/]+)\s*[=:]\s*(.+)$", line)
        if not match:
            print(
                f"  Skipping unparseable name override ({NAME_OVERRIDES_PATH.name}:{lineno}): {raw_line!r}",
                file=sys.stderr,
            )
            continue
        callsign = match.group(1).strip().upper()
        name = match.group(2).strip()
        if name:
            overrides[callsign] = name
    return overrides


def apply_name_overrides(members: list[dict], overrides: dict[str, str]) -> None:
    """Replace member['name'] with a name-overrides.txt entry, in place.

    Matches on the roster callsign (case-insensitive). Applied before the QRZ
    lookup so it needs no network/credentials. Logs each applied override and
    any override whose callsign isn't (yet) in the roster.
    """
    if not overrides:
        return
    used: set[str] = set()
    for member in members:
        key = member["callsign"].upper()
        new_name = overrides.get(key)
        if new_name and new_name != member["name"]:
            print(
                f"  Name override: {member['callsign']} {member['name']!r} -> {new_name!r}",
                file=sys.stderr,
            )
            member["name"] = new_name
            used.add(key)
        elif new_name:
            used.add(key)
    for key in overrides.keys() - used:
        print(
            f"  Name override for {key} not applied (callsign not in roster)",
            file=sys.stderr,
        )


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
    """Look up a callsign. Returns {'current_call', 'state', 'country', 'image'}.

    'current_call' is QRZ's canonical <call> element, which differs from the
    queried callsign for retired/aliased/vanity calls; callers use it to remap
    roster entries to the operator's current callsign. 'state' is a two-letter
    US state code (US ops only); 'country' is QRZ's DXCC country name, used to
    group non-US ops by country in the territory leaderboard.
    """
    empty = {"current_call": None, "state": None, "country": None, "image": None}
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

    # QRZ returns the operator's canonical <call>, which may differ from the
    # queried callsign for retired/aliased/vanity calls. Use it as the
    # authoritative current callsign.
    current_call = None
    call_elem = call.find("q:call", QRZ_NS)
    if call_elem is not None and call_elem.text:
        candidate = call_elem.text.strip().upper()
        if re.fullmatch(r"[A-Z0-9/]+", candidate):
            current_call = candidate

    state = None
    state_elem = call.find("q:state", QRZ_NS)
    if state_elem is not None and state_elem.text:
        text = state_elem.text.strip().upper()
        if re.fullmatch(r"[A-Z]{2}", text):
            state = text

    country = None
    country_elem = call.find("q:country", QRZ_NS)
    if country_elem is not None and country_elem.text:
        country = country_elem.text.strip() or None

    image = None
    image_elem = call.find("q:image", QRZ_NS)
    if image_elem is not None and image_elem.text:
        candidate = image_elem.text.strip()
        if candidate.startswith(("http://", "https://")):
            image = candidate

    return {"current_call": current_call, "state": state, "country": country, "image": image}


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


def mark_territory_ogs(members: list[dict]) -> None:
    """Badge the earliest member (lowest BKG #) in each map territory, in place.

    The first member in each US map state gets member['state_og'], and the
    first from each DX country gets member['country_og'] — the international
    counterpart of the state OG badge.
    """
    earliest: dict[tuple[str, str], dict] = {}
    for member in sorted(members, key=lambda m: m["number"]):
        bucket = member_map_bucket(member)
        if bucket and bucket not in earliest:
            earliest[bucket] = member
    for (kind, _territory), member in earliest.items():
        member["state_og" if kind == "state" else "country_og"] = True


def annotate_qrz(members: list[dict]) -> None:
    """Set member['state'], member['country'], member['state_og'],
    member['country_og'], and member['mugshot_path'] in place.

    Requires env vars QRZ_USERNAME and QRZ_PASSWORD (an XML-subscription QRZ
    account). Raises RuntimeError if creds are missing or login fails.
    """
    for member in members:
        member["state"] = None
        member["country"] = None
        member["state_og"] = False
        member["country_og"] = False
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
        # Remap to the operator's current callsign if QRZ reports a different
        # canonical <call> (e.g. after a vanity/retired-call change).
        current_call = info.get("current_call")
        if current_call and current_call != member["callsign"].upper():
            print(
                f"  Callsign updated: {member['callsign']} -> {current_call}",
                file=sys.stderr,
            )
            member["callsign"] = current_call
        member["state"] = info["state"]
        member["country"] = info["country"]
        override = local_override_mugshot(member["callsign"])
        if override:
            member["mugshot_path"] = override
        elif info["image"]:
            member["mugshot_path"] = download_mugshot(member["callsign"], info["image"])
    resolved = sum(1 for m in members if member_map_bucket(m))
    dx = sum(1 for m in members if (member_map_bucket(m) or ("",))[0] == "dx")
    mugshots = sum(1 for m in members if m.get("mugshot_path"))
    print(
        f"  QRZ placed {resolved}/{len(members)} members on the map ({dx} international)",
        file=sys.stderr,
    )
    print(f"  Mugshot resolved for {mugshots}/{len(members)} members (local overrides preferred)", file=sys.stderr)

    mark_territory_ogs(members)


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


def territory_og_badge_html(member: dict) -> str:
    """Corner ribbon for the first BKG member in a US state or DX country.

    State ribbons show the state code ("UT OG"); country ribbons show the
    country's flag emoji ("🇨🇦 OG") so long DXCC names don't blow out the
    ribbon, with the full name in the hover title.
    """
    if member.get("state_og"):
        label = html_escape(member.get("state") or "")
        title = label
    elif member.get("country_og"):
        country = (member.get("country") or "").strip()
        label = COUNTRY_FLAGS.get(country.lower(), "🌍")
        title = html_escape(country)
    else:
        return ""
    return f'\n                    <div class="state-og-badge" title="{title} OG">{label} OG</div>'


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
        '                            PHOTO<br>PENDING\n'
        '                        </div>'
    )


def render_founder_card(member: dict) -> str:
    callsign = html_escape(member["callsign"])
    name = html_escape(member["name"])
    number = f"BKG #{member['number']:03d}"
    territory_og_html = territory_og_badge_html(member)
    mugshot_inner = mugshot_inner_html(member)
    return f"""                <!-- FOUNDER - {callsign} - THE OG BRASS POUNDER -->
                <div class="member-card founder-card">{territory_og_html}
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
                        <div class="founder-quote">"2m CW or BUST"</div>
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
    badge_html += territory_og_badge_html(member)
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


def resolve_sponsors(members: list[dict]) -> None:
    """Resolve each member's raw "Sponsor" value to the sponsoring member in place.

    A sponsor may be recorded as a callsign ("KI7QCF") or a BKG number ("12",
    "BKG12", "BKG #12"). Sets member['sponsor_member'] to the matched member's
    dict, or None for a root / unrecognized sponsor. Stored as a reference (not
    a callsign string) so the later annotate_qrz() canonical-callsign remap
    can't leave sponsor links dangling on the old callsign.
    """
    by_call = {m["callsign"].upper(): m for m in members}
    by_num = {m["number"]: m for m in members}
    for member in members:
        raw = (member.get("sponsor_raw") or "").strip()
        if not raw:
            continue
        # Prefer an exact callsign match before parsing a number, so a callsign
        # like "K5OHY" isn't mistaken for member number 5.
        sponsor = by_call.get(raw.upper())
        if sponsor is None:
            num = parse_member_number(raw)
            sponsor = by_num.get(num) if num else None
        if sponsor is None:
            print(f"  Unrecognized sponsor for {member['callsign']}: {raw!r}", file=sys.stderr)
        elif sponsor is member:
            print(f"  Ignoring self-sponsor for {member['callsign']}", file=sys.stderr)
        else:
            member["sponsor_member"] = sponsor
    resolved = sum(1 for m in members if m.get("sponsor_member"))
    print(f"  Resolved sponsor for {resolved}/{len(members)} members", file=sys.stderr)


def render_downline_data(members: list[dict]) -> str:
    """Build the JSON downline data: flat list of {call, name, num, sponsor}.

    'sponsor' is the sponsoring member's callsign or null (a root). The tree
    in tree.html (#bkg-downline-data) assembles the forest client-side.
    """
    nodes = [
        {
            "call": m["callsign"],
            "name": m["name"],
            "num": m["number"],
            "sponsor": m["sponsor_member"]["callsign"] if m.get("sponsor_member") else None,
        }
        for m in sorted(members, key=lambda m: m["number"])
    ]
    return json.dumps(nodes, separators=(",", ":"))


def render_map_data(members: list[dict]) -> str:
    """Build the JSON map data consumed by the territory map (#bkg-map-data):

    {"states": {state_abbr: [{"call", "name", "num"}, ...]},
     "dx": {country: {"flag": "🇨🇦", "members": [{"call", "name", "num"}, ...]}}}

    US members land in "states" (keyed by QRZ state); international members
    land in "dx" (keyed by QRZ country) and render in the map's DX inset box.
    """
    by_state: dict[str, list[dict]] = {}
    by_country: dict[str, list[dict]] = {}
    for member in members:
        bucket = member_map_bucket(member)
        if not bucket:
            continue
        entry = {
            "call": member["callsign"],
            "name": member["name"],
            "num": member["number"],
        }
        kind, key = bucket
        target = by_state if kind == "state" else by_country
        target.setdefault(key, []).append(entry)
    for entries in (*by_state.values(), *by_country.values()):
        entries.sort(key=lambda e: e["num"])
    data = {
        "states": {state: by_state[state] for state in sorted(by_state)},
        "dx": {
            country: {
                "flag": COUNTRY_FLAGS.get(country.lower(), "🌍"),
                "members": by_country[country],
            }
            for country in sorted(by_country)
        },
    }
    return json.dumps(data, separators=(",", ":"))


US_STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

def replace_between(html: str, start_marker: str, end_marker: str, replacement: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    if not pattern.search(html):
        raise RuntimeError(f"Markers not found: {start_marker} ... {end_marker}")
    # Use a function replacement so backslashes in `replacement` (e.g. \uXXXX
    # in the JSON map data) are inserted literally instead of being treated as
    # regex backreferences/escapes.
    new_block = start_marker + replacement + end_marker
    return pattern.sub(lambda _match: new_block, html, count=1)


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
    html = replace_between(
        html,
        "<!-- MAP_DATA:START -->",
        "<!-- MAP_DATA:END -->",
        render_map_data(members),
    )
    INDEX_PATH.write_text(html)


def update_tree(members: list[dict]) -> None:
    """Inject the downline JSON into tree.html. No-op if tree.html is absent."""
    if not TREE_PATH.is_file():
        print(f"  {TREE_PATH.name} not found, skipping downline build", file=sys.stderr)
        return
    html = TREE_PATH.read_text()
    html = replace_between(
        html,
        "<!-- DOWNLINE_DATA:START -->",
        "<!-- DOWNLINE_DATA:END -->",
        render_downline_data(members),
    )
    TREE_PATH.write_text(html)


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

    overrides = load_name_overrides()
    if overrides:
        print(f"Applying {len(overrides)} name override(s) from {NAME_OVERRIDES_PATH.name}")
        apply_name_overrides(members, overrides)

    print("Resolving sponsors for the downline tree")
    resolve_sponsors(members)

    print("Looking up location + mugshot for each member via QRZ XML API")
    annotate_qrz(members)
    state_ogs = sum(1 for m in members if m.get("state_og"))
    country_ogs = sum(1 for m in members if m.get("country_og"))
    print(f"Marked {state_ogs} state OG(s) + {country_ogs} country OG(s) on the map")

    update_index(members)
    print(f"Updated {INDEX_PATH.name}")

    update_tree(members)
    print(f"Updated {TREE_PATH.name}")

    MEMBERS_TXT_PATH.write_text(render_members_txt(members))
    print(f"Wrote {MEMBERS_TXT_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
