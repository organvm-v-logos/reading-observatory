"""Pipeline orchestration for reading-observatory.

Runs the full fetch-deduplicate-score pipeline:
1. Load bibliographies → extract tags
2. Load essay tags from essays-index.json
3. Build vocabulary
4. Parse OPML → fetch feeds → deduplicate
5. Score items against vocabulary
6. Archive expired surfaced items
7. Write outputs (surfaced.json, seen.json)

CLI: python -m src.aggregator [--dry-run] [--essays-index PATH]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.bibliographies import extract_tags, load_all_bibliographies
from src.config import ObservatoryConfig
from src.feeds import deduplicate, fetch_all_feeds, load_seen, parse_opml, save_seen
from src.matcher import build_vocabulary, score_items


def load_essay_tags(path: str | Path) -> set[str]:
    """Load tag strings from essays-index.json. Returns empty set if missing."""
    path = Path(path)
    if not path.exists():
        return set()
    try:
        with open(path) as f:
            data = json.load(f)
        tag_freq = data.get("tag_frequency", {})
        return set(tag_freq.keys())
    except (json.JSONDecodeError, KeyError):
        return set()


def archive_expired(
    surfaced_path: str | Path,
    archive_dir: str | Path,
    expiry_days: int = 30,
) -> int:
    """Move expired items from surfaced.json to archive. Returns count archived."""
    surfaced_path = Path(surfaced_path)
    archive_dir = Path(archive_dir)

    if not surfaced_path.exists():
        return 0

    try:
        with open(surfaced_path) as f:
            items = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return 0

    if not items:
        return 0

    now = datetime.now(timezone.utc)
    keep = []
    expired = []

    for item in items:
        surfaced_date = item.get("surfaced_date", "")
        if surfaced_date:
            try:
                item_date = datetime.fromisoformat(surfaced_date)
                if hasattr(item_date, "tzinfo") and item_date.tzinfo is None:
                    item_date = item_date.replace(tzinfo=timezone.utc)
                age_days = (now - item_date).days
                if age_days > expiry_days:
                    expired.append(item)
                    continue
            except ValueError:
                pass
        keep.append(item)

    if expired:
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_file = archive_dir / f"archived-{now.strftime('%Y-%m-%d')}.json"
        existing = []
        if archive_file.exists():
            with open(archive_file) as f:
                existing = json.load(f)
        with open(archive_file, "w") as f:
            json.dump(existing + expired, f, indent=2, ensure_ascii=False)
            f.write("\n")

        with open(surfaced_path, "w") as f:
            json.dump(keep, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return len(expired)


def _build_collection_tags(bibliographies: dict[str, list[dict]]) -> dict[str, set[str]]:
    """Build per-collection tag sets from bibliographies."""
    result: dict[str, set[str]] = {}
    for coll_name, entries in bibliographies.items():
        tags = set()
        for entry in entries:
            for tag in entry.get("tags", []):
                tags.add(tag.lower())
                if "-" in tag:
                    for part in tag.split("-"):
                        if len(part) > 2:
                            tags.add(part.lower())
        result[coll_name] = tags
    return result


def aggregate(config: ObservatoryConfig, dry_run: bool = False) -> dict:
    """Run the full aggregation pipeline. Returns summary dict."""
    paths = config.paths
    scoring = config.scoring

    # 1. Load bibliographies and extract tags
    bibliographies = load_all_bibliographies(paths.bibliographies_dir)
    bib_tags = extract_tags(bibliographies)
    total_bib_entries = sum(len(entries) for entries in bibliographies.values())

    # 2. Load essay tags
    essay_tags = load_essay_tags(paths.essays_index_path)

    # 3. Build vocabulary
    vocabulary = build_vocabulary(essay_tags, bib_tags)

    # 4. Build collection-specific tag sets
    collection_tags = _build_collection_tags(bibliographies)

    # 5. Parse OPML and fetch feeds
    subscriptions = parse_opml(paths.opml_path)
    total_feeds = sum(len(feeds) for feeds in subscriptions.values())

    if dry_run:
        # In dry-run mode, skip actual fetching
        return {
            "dry_run": True,
            "bibliographies": len(bibliographies),
            "bibliography_entries": total_bib_entries,
            "bib_tags": len(bib_tags),
            "essay_tags": len(essay_tags),
            "vocabulary_size": len(vocabulary),
            "feeds": total_feeds,
            "collections": list(subscriptions.keys()),
        }

    all_items: list[dict] = []
    fetched = fetch_all_feeds(subscriptions, timeout=scoring.fetch_timeout)
    for collection_items in fetched.values():
        all_items.extend(collection_items)

    # 6. Deduplicate
    seen = load_seen(paths.seen_path)
    new_items = deduplicate(all_items, seen)

    # 7. Score
    scored = score_items(new_items, vocabulary, collection_tags, scoring.min_score)

    # 8. Archive expired items
    archived_count = archive_expired(
        paths.surfaced_path, paths.archive_dir, scoring.expiry_days
    )

    # 9. Load existing surfaced items and merge
    surfaced_path = Path(paths.surfaced_path)
    existing_surfaced = []
    if surfaced_path.exists():
        try:
            with open(surfaced_path) as f:
                existing_surfaced = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_surfaced = []

    # Tag new items with surfaced date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for item in scored:
        item["surfaced_date"] = today

    # Merge and cap at max_surfaced
    merged = existing_surfaced + scored
    merged = merged[:scoring.max_surfaced]

    # 10. Write outputs
    surfaced_path.parent.mkdir(parents=True, exist_ok=True)
    with open(surfaced_path, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write("\n")

    save_seen(paths.seen_path, seen)

    return {
        "dry_run": False,
        "bibliographies": len(bibliographies),
        "bibliography_entries": total_bib_entries,
        "bib_tags": len(bib_tags),
        "essay_tags": len(essay_tags),
        "vocabulary_size": len(vocabulary),
        "feeds": total_feeds,
        "items_fetched": len(all_items),
        "items_new": len(new_items),
        "items_scored": len(scored),
        "items_surfaced": len(merged),
        "items_archived": archived_count,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run the reading-observatory feed aggregation pipeline"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Load config and vocabularies without fetching feeds"
    )
    parser.add_argument(
        "--essays-index", default=None,
        help="Path to essays-index.json (overrides default)"
    )
    parser.add_argument(
        "--config", default=None,
        help="Path to scoring.yaml (overrides default)"
    )
    args = parser.parse_args()

    if args.config:
        config = ObservatoryConfig.from_yaml(args.config)
    else:
        config = ObservatoryConfig.default()

    if args.essays_index:
        config.paths.essays_index_path = args.essays_index

    summary = aggregate(config, dry_run=args.dry_run)

    if summary["dry_run"]:
        print(
            f"Dry run: {summary['bibliographies']} collections, "
            f"{summary['bibliography_entries']} entries, "
            f"{summary['vocabulary_size']} vocabulary terms, "
            f"{summary['feeds']} feeds"
        )
    else:
        print(
            f"Aggregated: {summary['items_fetched']} fetched, "
            f"{summary['items_new']} new, "
            f"{summary['items_scored']} scored above threshold, "
            f"{summary['items_surfaced']} surfaced, "
            f"{summary['items_archived']} archived"
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
