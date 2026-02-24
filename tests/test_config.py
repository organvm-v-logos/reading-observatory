"""Tests for configuration management."""

from pathlib import Path

from src.config import (
    VALID_COLLECTIONS,
    ObservatoryConfig,
    PathsConfig,
    ScoringConfig,
)

SCORING_YAML = Path(__file__).parent.parent / "config" / "scoring.yaml"


class TestScoringConfig:
    def test_default_values(self):
        config = ScoringConfig()
        assert config.min_score == 0.3
        assert config.expiry_days == 30
        assert config.max_surfaced == 25
        assert config.fetch_timeout == 10

    def test_from_yaml(self):
        config = ScoringConfig.from_yaml(SCORING_YAML)
        assert config.min_score == 0.3
        assert config.expiry_days == 30
        assert config.max_surfaced == 25

    def test_from_yaml_missing_file(self, tmp_path):
        config = ScoringConfig.from_yaml(tmp_path / "nonexistent.yaml")
        assert config.min_score == 0.3

    def test_from_yaml_custom_values(self, tmp_path):
        custom = tmp_path / "custom.yaml"
        custom.write_text("min_score: 0.5\nexpiry_days: 14\nmax_surfaced: 10\n")
        config = ScoringConfig.from_yaml(custom)
        assert config.min_score == 0.5
        assert config.expiry_days == 14
        assert config.max_surfaced == 10

    def test_default_classmethod(self):
        config = ScoringConfig.default()
        assert config.min_score == 0.3


class TestPathsConfig:
    def test_default_values(self):
        paths = PathsConfig.default()
        assert paths.bibliographies_dir == "bibliographies"
        assert paths.feeds_dir == "feeds"
        assert paths.opml_path == "feeds/subscriptions.opml"
        assert paths.seen_path == "feeds/seen.json"
        assert paths.surfaced_path == "feeds/surfaced.json"
        assert paths.archive_dir == "feeds/archive"


class TestValidCollections:
    def test_four_collections(self):
        assert len(VALID_COLLECTIONS) == 4

    def test_expected_names(self):
        assert "systems-thinking" in VALID_COLLECTIONS
        assert "creative-practice" in VALID_COLLECTIONS
        assert "institutional-design" in VALID_COLLECTIONS
        assert "ai-human-collaboration" in VALID_COLLECTIONS


class TestObservatoryConfig:
    def test_default(self):
        config = ObservatoryConfig.default()
        assert config.scoring.min_score == 0.3
        assert config.paths.feeds_dir == "feeds"

    def test_from_yaml(self):
        config = ObservatoryConfig.from_yaml(SCORING_YAML)
        assert config.scoring.min_score == 0.3
        assert config.paths.bibliographies_dir == "bibliographies"
