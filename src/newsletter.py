"""Weekly curated reading list generator for reading-observatory.

Transforms surfaced high-relevance articles into a Markdown newsletter format.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def generate_newsletter(surfaced_path: str, output_path: str = None) -> str:
    """Generate a Markdown newsletter from surfaced articles."""
    p = Path(surfaced_path)
    if not p.exists():
        print(f"Error: {surfaced_path} not found", file=sys.stderr)
        return ""

    try:
        items = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        print(f"Error parsing {surfaced_path}: {e}", file=sys.stderr)
        return ""

    if not items:
        print("No items surfaced this period.", file=sys.stderr)
        return ""

    # Sort by score descending
    items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# ORGAN-V: Weekly Reading List ({today})",
        "",
        "A curated selection of high-signal articles surfaced by the Logos Reading Observatory.",
        "",
    ]

    for item in items:
        title = item.get("title", "Untitled")
        url = item.get("url", "#")
        score = item.get("relevance_score", 0)
        summary = item.get("summary", "").strip()
        matched = item.get("matched_terms", [])

        # Format tags
        tags_str = ", ".join([f"`{t}`" for t in matched[:5]])

        lines.append(f"## [{title}]({url})")
        lines.append(f"**Score:** {score:.2f} | **Signal:** {tags_str}")
        lines.append("")
        if summary:
            # Simple truncation if too long
            if len(summary) > 500:
                summary = summary[:497] + "..."
            lines.append(f"> {summary}")
            lines.append("")
        lines.append("---")
        lines.append("")

    content = "\n".join(lines)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content)
        return str(out)

    return content


def main():
    parser = argparse.ArgumentParser(description="Generate curated reading list newsletter")
    parser.add_argument("--surfaced", required=True, help="Path to surfaced.json")
    parser.add_argument("--output", help="Output Markdown file path")
    args = parser.parse_args()

    result = generate_newsletter(args.surfaced, args.output)
    if result:
        if args.output:
            print(f"Newsletter generated: {result}")
        else:
            print(result)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
