"""Tests for bibliography loading, validation, and tag extraction."""

from pathlib import Path

from src.bibliographies import (
    extract_tags,
    load_all_bibliographies,
    load_bibliography,
    validate_all,
    validate_entry,
)

FIXTURES = Path(__file__).parent / "fixtures"
BIBLIOGRAPHIES = Path(__file__).parent.parent / "bibliographies"


class TestLoadBibliography:
    def test_load_valid_file(self):
        entries = load_bibliography(FIXTURES / "valid-bibliography.yaml")
        assert len(entries) == 2
        assert entries[0]["title"] == "Thinking in Systems: A Primer"

    def test_load_empty_file(self, tmp_path):
        empty = tmp_path / "empty.yaml"
        empty.write_text("")
        entries = load_bibliography(empty)
        assert entries == []


class TestValidateEntry:
    def test_valid_entry(self):
        entry = {
            "title": "Test Book",
            "author": "Test Author",
            "year": 2020,
            "relevance": "A" * 50,
            "tags": ["test-tag"],
            "collections": ["systems-thinking"],
        }
        errors = validate_entry(entry)
        assert errors == []

    def test_missing_required_fields(self):
        entry = {"title": "Only Title"}
        errors = validate_entry(entry)
        assert any("missing required field: author" in e for e in errors)
        assert any("missing required field: year" in e for e in errors)
        assert any("missing required field: relevance" in e for e in errors)
        assert any("missing required field: tags" in e for e in errors)
        assert any("missing required field: collections" in e for e in errors)

    def test_short_relevance(self):
        entry = {
            "title": "Test",
            "author": "Author",
            "year": 2020,
            "relevance": "Too short",
            "tags": ["tag"],
            "collections": ["systems-thinking"],
        }
        errors = validate_entry(entry)
        assert any("at least 50 characters" in e for e in errors)

    def test_empty_tags(self):
        entry = {
            "title": "Test",
            "author": "Author",
            "year": 2020,
            "relevance": "A" * 50,
            "tags": [],
            "collections": ["systems-thinking"],
        }
        errors = validate_entry(entry)
        assert any("at least 1 item" in e for e in errors)

    def test_invalid_collection(self):
        entry = {
            "title": "Test",
            "author": "Author",
            "year": 2020,
            "relevance": "A" * 50,
            "tags": ["tag"],
            "collections": ["nonexistent"],
        }
        errors = validate_entry(entry)
        assert any("invalid collection: nonexistent" in e for e in errors)

    def test_year_must_be_integer(self):
        entry = {
            "title": "Test",
            "author": "Author",
            "year": "not-a-number",
            "relevance": "A" * 50,
            "tags": ["tag"],
            "collections": ["systems-thinking"],
        }
        errors = validate_entry(entry)
        assert any("year must be an integer" in e for e in errors)

    def test_title_must_be_string(self):
        entry = {
            "title": 12345,
            "author": "Author",
            "year": 2020,
            "relevance": "A" * 50,
            "tags": ["tag"],
            "collections": ["systems-thinking"],
        }
        errors = validate_entry(entry)
        assert any("title must be a string" in e for e in errors)


class TestLoadAllBibliographies:
    def test_loads_from_directory(self):
        bibs = load_all_bibliographies(BIBLIOGRAPHIES)
        assert "systems-thinking" in bibs
        assert "creative-practice" in bibs
        assert "institutional-design" in bibs
        assert "ai-human-collaboration" in bibs

    def test_correct_entry_counts(self):
        bibs = load_all_bibliographies(BIBLIOGRAPHIES)
        assert len(bibs["systems-thinking"]) == 5
        assert len(bibs["creative-practice"]) == 4
        assert len(bibs["institutional-design"]) == 4
        assert len(bibs["ai-human-collaboration"]) == 4


class TestExtractTags:
    def test_extracts_unique_tags(self):
        bibs = {"test": [
            {"tags": ["a", "b"]},
            {"tags": ["b", "c"]},
        ]}
        tags = extract_tags(bibs)
        assert tags == {"a", "b", "c"}

    def test_empty_bibliographies(self):
        tags = extract_tags({})
        assert tags == set()

    def test_real_bibliographies_have_tags(self):
        bibs = load_all_bibliographies(BIBLIOGRAPHIES)
        tags = extract_tags(bibs)
        assert "systems-thinking" in tags
        assert "cybernetics" in tags
        assert "governance" in tags


class TestValidateAll:
    def test_valid_bibliographies_pass(self):
        errors = validate_all(BIBLIOGRAPHIES)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_fixture_with_errors(self):
        errors = validate_all(FIXTURES)
        assert len(errors) > 0
