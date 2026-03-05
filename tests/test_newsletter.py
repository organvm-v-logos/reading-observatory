"""Tests for the newsletter generator."""

import json
from unittest.mock import patch

from src.newsletter import generate_newsletter, main


class TestNewsletterGenerator:
    def test_generates_valid_markdown(self, tmp_path):
        surfaced = tmp_path / "surfaced.json"
        items = [
            {
                "title": "Test Article",
                "url": "https://example.com/test",
                "relevance_score": 0.85,
                "summary": "This is a summary of the test article.",
                "matched_terms": ["governance", "systems"],
            }
        ]
        surfaced.write_text(json.dumps(items))

        output = tmp_path / "newsletter.md"
        result_path = generate_newsletter(str(surfaced), str(output))

        assert result_path == str(output)
        content = output.read_text()
        assert "# ORGAN-V: Weekly Reading List" in content
        assert "## [Test Article](https://example.com/test)" in content
        assert "**Score:** 0.85" in content
        assert "`governance`" in content

    def test_handles_empty_items(self, tmp_path):
        surfaced = tmp_path / "empty.json"
        surfaced.write_text("[]")
        result = generate_newsletter(str(surfaced))
        assert result == ""

    def test_handles_missing_file(self, tmp_path):
        result = generate_newsletter(str(tmp_path / "missing.json"))
        assert result == ""


class TestNewsletterMain:
    @patch("src.newsletter.generate_newsletter")
    @patch("sys.exit")
    def test_main_runs(self, mock_exit, mock_gen, tmp_path):
        mock_gen.return_value = "newsletter.md"
        with patch("sys.argv", ["prog", "--surfaced", "surf.json", "--output", "out.md"]):
            main()
        mock_exit.assert_called_with(0)
