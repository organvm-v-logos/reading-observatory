"""Bibliography loading, validation, and tag extraction.

Loads YAML bibliography files, validates entries against the schema
defined in ADR-001, and extracts tags for vocabulary building.

CLI: python -m src.bibliographies --validate bibliographies/
"""

import argparse
import sys
from pathlib import Path

import yaml

from src.config import VALID_COLLECTIONS

REQUIRED_FIELDS = ("title", "author", "year", "relevance", "tags", "collections")


def load_bibliography(path: str | Path) -> list[dict]:
    """Load a single bibliography YAML file and return list of entry dicts."""
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)
    if data is None:
        return []
    if not isinstance(data, list):
        return [data]
    return data


def validate_entry(entry: dict) -> list[str]:
    """Validate a single bibliography entry. Returns list of error strings."""
    errors = []

    for field in REQUIRED_FIELDS:
        if field not in entry:
            errors.append(f"missing required field: {field}")

    if "title" in entry and not isinstance(entry["title"], str):
        errors.append("title must be a string")

    if "author" in entry and not isinstance(entry["author"], str):
        errors.append("author must be a string")

    if "year" in entry:
        if not isinstance(entry["year"], int):
            errors.append("year must be an integer")

    if "relevance" in entry:
        if not isinstance(entry["relevance"], str):
            errors.append("relevance must be a string")
        elif len(entry["relevance"].strip()) < 50:
            errors.append("relevance must be at least 50 characters")

    if "tags" in entry:
        if not isinstance(entry["tags"], list):
            errors.append("tags must be a list")
        elif len(entry["tags"]) < 1:
            errors.append("tags must have at least 1 item")

    if "collections" in entry:
        if not isinstance(entry["collections"], list):
            errors.append("collections must be a list")
        elif len(entry["collections"]) < 1:
            errors.append("collections must have at least 1 item")
        else:
            for coll in entry["collections"]:
                if coll not in VALID_COLLECTIONS:
                    errors.append(f"invalid collection: {coll}")

    return errors


def load_all_bibliographies(bib_dir: str | Path) -> dict[str, list[dict]]:
    """Load all bibliography YAML files from a directory.

    Returns dict keyed by collection name (stem of filename).
    """
    bib_dir = Path(bib_dir)
    result = {}
    for path in sorted(bib_dir.glob("*.yaml")):
        result[path.stem] = load_bibliography(path)
    return result


def extract_tags(bibliographies: dict[str, list[dict]]) -> set[str]:
    """Extract all unique tags from all bibliography entries."""
    tags = set()
    for entries in bibliographies.values():
        for entry in entries:
            for tag in entry.get("tags", []):
                tags.add(tag)
    return tags


def validate_all(bib_dir: str | Path) -> list[str]:
    """Validate all bibliography entries in a directory. Returns all errors."""
    bib_dir = Path(bib_dir)
    errors = []
    for path in sorted(bib_dir.glob("*.yaml")):
        entries = load_bibliography(path)
        for i, entry in enumerate(entries):
            entry_errors = validate_entry(entry)
            for err in entry_errors:
                title = entry.get("title", f"entry {i}")
                errors.append(f"{path.name}: {title}: {err}")
    return errors


def validate_main():
    """CLI entrypoint: validate all bibliographies."""
    parser = argparse.ArgumentParser(description="Validate bibliography YAML files")
    parser.add_argument("--validate", required=True, help="Directory containing bibliography YAML")
    args = parser.parse_args()

    bib_dir = Path(args.validate)
    if not bib_dir.is_dir():
        print(f"Error: {bib_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    errors = validate_all(bib_dir)
    if errors:
        print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)
    else:
        yaml_files = list(bib_dir.glob("*.yaml"))
        total_entries = sum(len(load_bibliography(f)) for f in yaml_files)
        print(f"All {total_entries} entries in {len(yaml_files)} files valid")
        sys.exit(0)


if __name__ == "__main__":
    validate_main()
