"""Tests for feed parsing, fetching, and deduplication."""

from pathlib import Path

from src.feeds import (
    deduplicate,
    fetch_feed,
    hash_url,
    load_seen,
    parse_opml,
    save_seen,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseOpml:
    def test_parse_sample_opml(self):
        result = parse_opml(FIXTURES / "sample-subscriptions.opml")
        assert "systems-thinking" in result
        assert "creative-practice" in result
        assert len(result["systems-thinking"]) == 2
        assert len(result["creative-practice"]) == 1

    def test_feed_structure(self):
        result = parse_opml(FIXTURES / "sample-subscriptions.opml")
        feed = result["systems-thinking"][0]
        assert feed["title"] == "Test Feed A"
        assert feed["xml_url"] == "https://example.com/feed-a.xml"
        assert feed["html_url"] == "https://example.com/a"

    def test_parse_real_opml(self):
        opml_path = Path(__file__).parent.parent / "feeds" / "subscriptions.opml"
        result = parse_opml(opml_path)
        assert len(result) == 4
        total_feeds = sum(len(feeds) for feeds in result.values())
        assert total_feeds == 13


class TestHashUrl:
    def test_deterministic(self):
        url = "https://example.com/test"
        assert hash_url(url) == hash_url(url)

    def test_different_urls_different_hashes(self):
        assert hash_url("https://a.com") != hash_url("https://b.com")

    def test_returns_hex_string(self):
        result = hash_url("https://example.com")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)


class TestSeenPersistence:
    def test_save_and_load(self, tmp_path):
        seen_path = tmp_path / "seen.json"
        seen = {"abc123": "2026-02-17", "def456": "2026-02-18"}
        save_seen(seen_path, seen)
        loaded = load_seen(seen_path)
        assert loaded == seen

    def test_load_missing_file(self, tmp_path):
        result = load_seen(tmp_path / "nonexistent.json")
        assert result == {}

    def test_load_existing_fixture(self):
        seen = load_seen(FIXTURES / "seen-with-entries.json")
        assert len(seen) == 2


class TestFetchFeed:
    def test_fetch_rss_feed(self):
        feed_path = FIXTURES / "sample-feed.xml"
        items = fetch_feed(f"file://{feed_path}")
        assert len(items) == 2
        assert items[0]["title"] == "Systems Thinking in Software Architecture"
        assert items[0]["url"] == "https://example.com/systems-thinking-software"

    def test_fetch_atom_feed(self):
        feed_path = FIXTURES / "sample-atom.xml"
        items = fetch_feed(f"file://{feed_path}")
        assert len(items) == 1
        assert items[0]["title"] == "Cybernetics and Organizational Design"

    def test_fetch_malformed_feed(self):
        feed_path = FIXTURES / "malformed-feed.xml"
        items = fetch_feed(f"file://{feed_path}")
        # feedparser is lenient; may return partial results or empty
        assert isinstance(items, list)

    def test_fetch_nonexistent_url(self):
        items = fetch_feed("file:///nonexistent/path/feed.xml")
        assert items == []


class TestDeduplicate:
    def test_new_items_pass_through(self):
        items = [
            {"url": "https://example.com/1"},
            {"url": "https://example.com/2"},
        ]
        seen = {}
        result = deduplicate(items, seen)
        assert len(result) == 2
        assert len(seen) == 2

    def test_seen_items_filtered(self):
        items = [{"url": "https://example.com/1"}]
        seen = {hash_url("https://example.com/1"): "2026-02-17"}
        result = deduplicate(items, seen)
        assert len(result) == 0

    def test_mixed_new_and_seen(self):
        items = [
            {"url": "https://example.com/1"},
            {"url": "https://example.com/2"},
        ]
        seen = {hash_url("https://example.com/1"): "2026-02-17"}
        result = deduplicate(items, seen)
        assert len(result) == 1
        assert result[0]["url"] == "https://example.com/2"

    def test_items_without_url_skipped(self):
        items = [{"title": "No URL"}, {"url": ""}]
        seen = {}
        result = deduplicate(items, seen)
        assert len(result) == 0
