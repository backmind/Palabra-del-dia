"""Scrapes 'La Palabra del Día' from elcastellano.org and maintains an Atom feed."""

import datetime
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

FEED_PATH = Path(__file__).resolve().parent.parent / "feed.xml"
BASE_URL = "https://www.elcastellano.org/envios"
MAX_ENTRIES = 90

ATOM_NS = "http://www.w3.org/2005/Atom"
FEED_ID = "https://github.com/backmind/Palabra-del-dia"
FEED_TITLE = "La Palabra del Día — elcastellano.org"
FEED_SUBTITLE = "Etimología diaria de Ricardo Soca, sin publicidad"
FEED_SELF = "https://backmind.github.io/Palabra-del-dia/feed.xml"
FEED_ALT = "https://www.elcastellano.org"

ET.register_namespace("", ATOM_NS)

# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


def build_url(date: datetime.date) -> str:
    return f"{BASE_URL}/{date:%Y-%m-%d}-000000"


def fetch_page(date: datetime.date) -> BeautifulSoup | None:
    url = build_url(date)
    resp = httpx.get(url, follow_redirects=True, timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------


def _inner_html(tag) -> str | None:
    """Return the inner HTML of a BeautifulSoup tag, or None."""
    if tag is None:
        return None
    return tag.decode_contents().strip()


def _text(tag) -> str | None:
    if tag is None:
        return None
    return tag.get_text(strip=True)


def parse_entry(soup: BeautifulSoup, date: datetime.date) -> dict:
    # Clean out scripts, ads, iframes before parsing
    for junk in soup.select("script, iframe, ins, .ad"):
        junk.decompose()

    title_el = soup.select_one("h1.page-header")
    title = _text(title_el) or "Sin título"

    entry: dict = {"date": date, "title": title, "url": build_url(date)}

    # --- Palabra del día ---
    palabra = soup.select_one("article#group-palabra")
    if palabra:
        img = palabra.select_one("figure img")
        entry["image_url"] = img["src"] if img and img.get("src") else None
        entry["image_caption"] = _text(palabra.select_one("figcaption"))
        entry["palabra_body"] = _inner_html(
            palabra.select_one(".field-name-body .field-item")
        )
    else:
        entry["image_url"] = None
        entry["image_caption"] = None
        entry["palabra_body"] = None

    # --- Medievalismo ---
    med = soup.select_one("article#group-medievalismo")
    if med:
        entry["medievalismo_title"] = _text(
            med.select_one(".field-name-field-medievalismo h2")
        )
        med_img = med.select_one("figure img")
        entry["medievalismo_image_url"] = (
            med_img["src"] if med_img and med_img.get("src") else None
        )
        entry["medievalismo_image_caption"] = _text(med.select_one("figcaption"))
        entry["medievalismo_body"] = _inner_html(
            med.select_one(".field-name-field-cuerpo-del-medievalismo .field-item")
        )
    else:
        entry["medievalismo_title"] = None
        entry["medievalismo_image_url"] = None
        entry["medievalismo_image_caption"] = None
        entry["medievalismo_body"] = None

    # --- Píldoras de lenguaje ---
    consulta = soup.select_one("article#group-consulta")
    if consulta:
        entry["consulta_question"] = _inner_html(
            consulta.select_one(".field-name-field-pregunta .field-item")
        )
        entry["consulta_answer"] = _inner_html(
            consulta.select_one(".field-name-field-respuesta .field-item")
        )
    else:
        entry["consulta_question"] = None
        entry["consulta_answer"] = None

    # --- Latín del día ---
    latin = soup.select_one("article#group-latin")
    if latin:
        entry["latin_phrase"] = _inner_html(
            latin.select_one(".field-name-field-lat-n .field-item")
        )
        entry["latin_translation"] = _inner_html(
            latin.select_one(".field-name-field-cuerpo-del-lat-n .field-item")
        )
    else:
        entry["latin_phrase"] = None
        entry["latin_translation"] = None

    return entry


# ---------------------------------------------------------------------------
# Build HTML content for feed entry
# ---------------------------------------------------------------------------


def build_entry_html(entry: dict) -> str:
    parts: list[str] = []

    # Palabra del día
    if entry.get("image_url"):
        caption = entry.get("image_caption") or ""
        parts.append(
            f'<figure><img src="{entry["image_url"]}" alt="{entry["title"]}"/>'
            f"<figcaption>{caption}</figcaption></figure>"
        )
    if entry.get("palabra_body"):
        parts.append(entry["palabra_body"])

    # Medievalismo
    if entry.get("medievalismo_title"):
        parts.append("<hr/>")
        parts.append(f'<h3>Medievalismo: {entry["medievalismo_title"]}</h3>')
        if entry.get("medievalismo_image_url"):
            caption = entry.get("medievalismo_image_caption") or ""
            parts.append(
                f'<figure><img src="{entry["medievalismo_image_url"]}" alt="{entry["medievalismo_title"]}"/>'
                f"<figcaption>{caption}</figcaption></figure>"
            )
        if entry.get("medievalismo_body"):
            parts.append(entry["medievalismo_body"])

    # Píldoras
    if entry.get("consulta_question"):
        parts.append("<hr/>")
        parts.append("<h3>Píldoras de lenguaje</h3>")
        parts.append(f'<blockquote>{entry["consulta_question"]}</blockquote>')
        if entry.get("consulta_answer"):
            parts.append(entry["consulta_answer"])

    # Latín
    if entry.get("latin_phrase"):
        parts.append("<hr/>")
        parts.append("<h3>Latín del día</h3>")
        parts.append(f'<p><em>{entry["latin_phrase"]}</em></p>')
        if entry.get("latin_translation"):
            parts.append(entry["latin_translation"])

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Atom feed helpers
# ---------------------------------------------------------------------------


def _atom(tag: str) -> str:
    return f"{{{ATOM_NS}}}{tag}"


def load_feed() -> ET.ElementTree | None:
    if FEED_PATH.exists():
        return ET.parse(FEED_PATH)
    return None


def entry_exists(tree: ET.ElementTree, date: datetime.date) -> bool:
    date_str = f"{date:%Y-%m-%d}"
    for entry_id in tree.iter(_atom("id")):
        if entry_id.text and date_str in entry_id.text:
            return True
    return False


def _make_feed_skeleton() -> ET.Element:
    feed = ET.Element(_atom("feed"))
    ET.SubElement(feed, _atom("title")).text = FEED_TITLE
    ET.SubElement(feed, _atom("subtitle")).text = FEED_SUBTITLE
    ET.SubElement(feed, _atom("id")).text = FEED_ID
    ET.SubElement(feed, _atom("link"), href=FEED_ALT, rel="alternate")
    ET.SubElement(feed, _atom("link"), href=FEED_SELF, rel="self")
    author = ET.SubElement(feed, _atom("author"))
    ET.SubElement(author, _atom("name")).text = "elcastellano.org"
    ET.SubElement(feed, _atom("updated"))
    return feed


def add_entry(tree: ET.ElementTree | None, entry: dict) -> ET.ElementTree:
    if tree is None:
        root = _make_feed_skeleton()
        tree = ET.ElementTree(root)
    root = tree.getroot()

    iso = f"{entry['date'].isoformat()}T00:00:00Z"

    # Update feed <updated>
    updated_el = root.find(_atom("updated"))
    if updated_el is not None:
        updated_el.text = iso

    # Build <entry>
    e = ET.Element(_atom("entry"))
    ET.SubElement(e, _atom("title")).text = entry["title"]
    ET.SubElement(e, _atom("id")).text = entry["url"]
    ET.SubElement(e, _atom("link"), href=entry["url"], rel="alternate")
    ET.SubElement(e, _atom("updated")).text = iso
    content = ET.SubElement(e, _atom("content"), type="html")
    content.text = entry["html"]

    # Insert after metadata elements, before other entries
    insert_pos = 0
    for i, child in enumerate(root):
        if child.tag == _atom("entry"):
            insert_pos = i
            break
    else:
        insert_pos = len(root)
    root.insert(insert_pos, e)

    return tree


def trim_entries(tree: ET.ElementTree, max_entries: int = MAX_ENTRIES) -> None:
    root = tree.getroot()
    entries = root.findall(_atom("entry"))
    if len(entries) > max_entries:
        for old in entries[max_entries:]:
            root.remove(old)


def save_feed(tree: ET.ElementTree) -> None:
    ET.indent(tree, space="  ")
    tree.write(str(FEED_PATH), encoding="unicode", xml_declaration=True)
    # Ensure trailing newline
    with open(FEED_PATH, "a", encoding="utf-8") as f:
        f.write("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    today = datetime.date.today()

    if today.weekday() >= 5:  # 5=Saturday, 6=Sunday
        print(f"{today} is a weekend. No newsletter today.")
        sys.exit(0)

    tree = load_feed()

    if tree and entry_exists(tree, today):
        print(f"Entry for {today} already exists. Skipping.")
        sys.exit(0)

    print(f"Fetching {build_url(today)} ...")
    soup = fetch_page(today)
    if soup is None:
        print(f"Page for {today} not found (404). Will retry later.")
        sys.exit(0)

    entry = parse_entry(soup, today)
    entry["html"] = build_entry_html(entry)

    tree = add_entry(tree, entry)
    trim_entries(tree)
    save_feed(tree)

    print(f"Feed updated: {entry['title']} ({today})")


if __name__ == "__main__":
    main()
