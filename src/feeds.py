"""Feed parsing, fetching, and deduplication.

Parses OPML subscription files, fetches RSS/Atom feeds via feedparser,
and deduplicates items using URL hashing.
"""

import hashlib
import json
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import feedparser


def parse_opml(path: str | Path) -> dict[str, list[dict]]:
    """Parse an OPML file into {collection: [{title, xml_url, html_url}]}.

    Expects a two-level outline: top-level outlines are collection groups,
    child outlines are individual feed subscriptions.
    """
    tree = ET.parse(str(path))
    root = tree.getroot()
    body = root.find("body")
    if body is None:
        return {}

    result: dict[str, list[dict]] = {}
    for group in body.findall("outline"):
        collection = group.get("text", group.get("title", "unknown"))
        feeds = []
        for outline in group.findall("outline"):
            xml_url = outline.get("xmlUrl", "")
            if xml_url:
                feeds.append(
                    {
                        "title": outline.get("title", outline.get("text", "")),
                        "xml_url": xml_url,
                        "html_url": outline.get("htmlUrl", ""),
                    }
                )
        if feeds:
            result[collection] = feeds
    return result


def hash_url(url: str) -> str:
    """Compute SHA-256 hash of a URL for deduplication."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def load_seen(path: str | Path) -> dict[str, str]:
    """Load the seen URL-hash → date mapping from JSON."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_seen(path: str | Path, seen: dict[str, str]) -> None:
    """Save the seen URL-hash → date mapping to JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(seen, f, indent=2, ensure_ascii=False)
        f.write("\n")


def fetch_feed(xml_url: str, timeout: int = 10) -> list[dict]:
    """Fetch a single RSS/Atom feed and return normalized items.

    Returns list of {title, url, author, published, summary}.
    Returns [] on any error.
    """
    try:
        headers = {"User-Agent": "reading-observatory/0.2"}
        req = urllib.request.Request(xml_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        parsed = feedparser.parse(raw)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return []
    except Exception:
        return []

    if parsed.bozo and not parsed.entries:
        return []

    items = []
    for entry in parsed.entries:
        url = entry.get("link", "")
        if not url:
            continue
        published = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
            except (TypeError, ValueError):
                pass
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).isoformat()
            except (TypeError, ValueError):
                pass
        items.append(
            {
                "title": entry.get("title", ""),
                "url": url,
                "author": entry.get("author", ""),
                "published": published,
                "summary": entry.get("summary", ""),
            }
        )
    return items


def fetch_all_feeds(
    subscriptions: dict[str, list[dict]],
    timeout: int = 10,
) -> dict[str, list[dict]]:
    """Fetch all feeds from parsed OPML subscriptions.

    Returns {collection: [items]} with each item tagged with its collection.
    """
    result: dict[str, list[dict]] = {}
    for collection, feeds in subscriptions.items():
        collection_items = []
        for feed in feeds:
            items = fetch_feed(feed["xml_url"], timeout=timeout)
            for item in items:
                item["collection"] = collection
                item["feed_title"] = feed["title"]
            collection_items.extend(items)
        if collection_items:
            result[collection] = collection_items
    return result


def deduplicate(
    items: list[dict],
    seen: dict[str, str],
) -> list[dict]:
    """Filter out already-seen items and update the seen dict.

    Returns only new items. Modifies seen dict in place.
    """
    new_items = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for item in items:
        url = item.get("url", "")
        if not url:
            continue
        url_hash = hash_url(url)
        if url_hash not in seen:
            seen[url_hash] = today
            new_items.append(item)
    return new_items
