"""Tests for the aggregation pipeline."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from src.aggregator import (
    _build_collection_tags,
    aggregate,
    archive_expired,
    load_essay_tags,
    main,
)
from src.config import ObservatoryConfig, PathsConfig, ScoringConfig

FIXTURES = Path(__file__).parent / "fixtures"


class TestAggregatorMain:
    @patch("src.aggregator.aggregate")
    @patch("sys.exit")
    def test_main_runs(self, mock_exit, mock_agg):
        mock_agg.return_value = {
            "dry_run": False,
            "items_fetched": 10,
            "items_new": 8,
            "items_scored": 5,
            "items_surfaced": 2,
            "items_archived": 0,
        }
        with patch("sys.argv", ["prog"]):
            main()
        mock_exit.assert_called_with(0)


class TestLoadEssayTags:
    def test_loads_tags_from_fixture(self):
        tags = load_essay_tags(FIXTURES / "essays-index-sample.json")
        assert "governance" in tags
        assert "methodology" in tags
        assert "systems-thinking" in tags

    def test_missing_file_returns_empty(self, tmp_path):
        tags = load_essay_tags(tmp_path / "nonexistent.json")
        assert tags == set()

    def test_malformed_json_returns_empty(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json")
        tags = load_essay_tags(bad)
        assert tags == set()


class TestArchiveExpired:
    def test_archives_old_items(self, tmp_path):
        surfaced_path = tmp_path / "surfaced.json"
        archive_dir = tmp_path / "archive"
        old_date = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d")
        items = [
            {"title": "Old", "surfaced_date": old_date},
            {"title": "Recent", "surfaced_date": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
        ]
        surfaced_path.write_text(json.dumps(items))

        count = archive_expired(surfaced_path, archive_dir, expiry_days=30)
        assert count == 1

        remaining = json.loads(surfaced_path.read_text())
        assert len(remaining) == 1
        assert remaining[0]["title"] == "Recent"

        archived_files = list(archive_dir.glob("archived-*.json"))
        assert len(archived_files) == 1

    def test_nothing_to_archive(self, tmp_path):
        surfaced_path = tmp_path / "surfaced.json"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        items = [{"title": "Fresh", "surfaced_date": today}]
        surfaced_path.write_text(json.dumps(items))

        count = archive_expired(surfaced_path, tmp_path / "archive", expiry_days=30)
        assert count == 0

    def test_missing_surfaced_file(self, tmp_path):
        count = archive_expired(tmp_path / "nope.json", tmp_path / "archive")
        assert count == 0

    def test_empty_surfaced_file(self, tmp_path):
        surfaced_path = tmp_path / "surfaced.json"
        surfaced_path.write_text("[]")
        count = archive_expired(surfaced_path, tmp_path / "archive")
        assert count == 0


class TestBuildCollectionTags:
    def test_extracts_collection_tags(self):
        bibs = {
            "systems-thinking": [{"tags": ["cybernetics", "feedback-loops"]}],
            "creative-practice": [{"tags": ["generative-art"]}],
        }
        result = _build_collection_tags(bibs)
        assert "cybernetics" in result["systems-thinking"]
        assert "feedback" in result["systems-thinking"]  # split from feedback-loops
        assert "loops" in result["systems-thinking"]
        assert "generative-art" in result["creative-practice"]


class TestAggregate:
    def test_dry_run(self, tmp_path):
        bib_dir = tmp_path / "bibliographies"
        bib_dir.mkdir()
        (bib_dir / "test.yaml").write_text(
            '- title: "Test"\n  author: "Author"\n  year: 2020\n'
            '  relevance: "' + "A" * 50 + '"\n'
            '  tags: ["test-tag"]\n  collections: ["systems-thinking"]\n'
        )

        feeds_dir = tmp_path / "feeds"
        feeds_dir.mkdir()
        opml = tmp_path / "subscriptions.opml"
        opml.write_text(
            '<?xml version="1.0"?><opml version="2.0"><head/><body>'
            '<outline text="test"><outline type="rss" title="Feed" '
            'xmlUrl="https://example.com/feed.xml" htmlUrl="https://example.com/"/>'
            "</outline></body></opml>"
        )

        config = ObservatoryConfig(
            scoring=ScoringConfig(),
            paths=PathsConfig(
                bibliographies_dir=str(bib_dir),
                feeds_dir=str(feeds_dir),
                opml_path=str(opml),
                seen_path=str(feeds_dir / "seen.json"),
                surfaced_path=str(feeds_dir / "surfaced.json"),
                archive_dir=str(feeds_dir / "archive"),
                essays_index_path=str(FIXTURES / "essays-index-sample.json"),
            ),
        )

        summary = aggregate(config, dry_run=True)
        assert summary["dry_run"] is True
        assert summary["bibliographies"] == 1
        assert summary["bibliography_entries"] == 1
        assert summary["vocabulary_size"] > 0
        assert summary["feeds"] == 1

    @patch("src.aggregator.fetch_all_feeds")
    def test_full_pipeline_mocked(self, mock_fetch, tmp_path):
        bib_dir = tmp_path / "bibliographies"
        bib_dir.mkdir()
        (bib_dir / "test.yaml").write_text(
            '- title: "Test"\n  author: "Author"\n  year: 2020\n'
            '  relevance: "' + "A" * 50 + '"\n'
            '  tags: ["governance"]\n  collections: ["systems-thinking"]\n'
        )

        feeds_dir = tmp_path / "feeds"
        feeds_dir.mkdir()
        (feeds_dir / "seen.json").write_text("{}")
        (feeds_dir / "surfaced.json").write_text("[]")
        (feeds_dir / "archive").mkdir()

        opml = tmp_path / "subscriptions.opml"
        opml.write_text(
            '<?xml version="1.0"?><opml version="2.0"><head/><body>'
            '<outline text="systems-thinking">'
            '<outline type="rss" title="Feed" '
            'xmlUrl="https://example.com/feed.xml" htmlUrl="https://example.com/"/>'
            "</outline></body></opml>"
        )

        mock_fetch.return_value = {
            "systems-thinking": [
                {
                    "title": "Governance and Systems Thinking",
                    "url": "https://example.com/governance-systems",
                    "summary": "About governance in complex systems thinking approaches.",
                    "author": "Test",
                    "published": "2026-02-17",
                    "collection": "systems-thinking",
                    "feed_title": "Feed",
                },
            ],
        }

        config = ObservatoryConfig(
            scoring=ScoringConfig(min_score=0.01),
            paths=PathsConfig(
                bibliographies_dir=str(bib_dir),
                feeds_dir=str(feeds_dir),
                opml_path=str(opml),
                seen_path=str(feeds_dir / "seen.json"),
                surfaced_path=str(feeds_dir / "surfaced.json"),
                archive_dir=str(feeds_dir / "archive"),
                essays_index_path=str(FIXTURES / "essays-index-sample.json"),
            ),
        )

        summary = aggregate(config, dry_run=False)
        assert summary["dry_run"] is False
        assert summary["items_fetched"] == 1
        assert summary["items_new"] == 1
        assert summary["items_scored"] >= 1

        surfaced = json.loads((feeds_dir / "surfaced.json").read_text())
        assert len(surfaced) >= 1
        assert surfaced[0]["title"] == "Governance and Systems Thinking"

    @patch("src.aggregator.fetch_all_feeds")
    def test_pipeline_with_no_feeds(self, mock_fetch, tmp_path):
        bib_dir = tmp_path / "bibliographies"
        bib_dir.mkdir()

        feeds_dir = tmp_path / "feeds"
        feeds_dir.mkdir()
        (feeds_dir / "seen.json").write_text("{}")
        (feeds_dir / "surfaced.json").write_text("[]")
        (feeds_dir / "archive").mkdir()

        opml = tmp_path / "subscriptions.opml"
        opml.write_text('<?xml version="1.0"?><opml version="2.0"><head/><body></body></opml>')

        mock_fetch.return_value = {}

        config = ObservatoryConfig(
            scoring=ScoringConfig(),
            paths=PathsConfig(
                bibliographies_dir=str(bib_dir),
                feeds_dir=str(feeds_dir),
                opml_path=str(opml),
                seen_path=str(feeds_dir / "seen.json"),
                surfaced_path=str(feeds_dir / "surfaced.json"),
                archive_dir=str(feeds_dir / "archive"),
                essays_index_path=str(tmp_path / "nonexistent.json"),
            ),
        )

        summary = aggregate(config, dry_run=False)
        assert summary["items_fetched"] == 0
        assert summary["items_new"] == 0
        assert summary["items_scored"] == 0
