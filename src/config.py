"""Configuration management for reading-observatory.

Loads scoring parameters and path defaults from YAML config.
All config objects expose `.from_yaml()` and `.default()` classmethods.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_COLLECTIONS = frozenset([
    "systems-thinking",
    "creative-practice",
    "institutional-design",
    "ai-human-collaboration",
])


@dataclass
class ScoringConfig:
    """Feed scoring parameters."""

    min_score: float = 0.3
    expiry_days: int = 30
    max_surfaced: int = 25
    fetch_timeout: int = 10

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ScoringConfig":
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(
            min_score=float(data.get("min_score", 0.3)),
            expiry_days=int(data.get("expiry_days", 30)),
            max_surfaced=int(data.get("max_surfaced", 25)),
            fetch_timeout=int(data.get("fetch_timeout", 10)),
        )

    @classmethod
    def default(cls) -> "ScoringConfig":
        config_path = Path(__file__).parent.parent / "config" / "scoring.yaml"
        return cls.from_yaml(config_path)


@dataclass
class PathsConfig:
    """Directory and file path defaults."""

    bibliographies_dir: str = "bibliographies"
    feeds_dir: str = "feeds"
    config_dir: str = "config"
    opml_path: str = "feeds/subscriptions.opml"
    seen_path: str = "feeds/seen.json"
    surfaced_path: str = "feeds/surfaced.json"
    archive_dir: str = "feeds/archive"
    essays_index_path: str = "../public-process/data/essays-index.json"

    @classmethod
    def default(cls) -> "PathsConfig":
        return cls()


@dataclass
class ObservatoryConfig:
    """Top-level configuration aggregating scoring + paths."""

    scoring: ScoringConfig
    paths: PathsConfig

    @classmethod
    def default(cls) -> "ObservatoryConfig":
        return cls(
            scoring=ScoringConfig.default(),
            paths=PathsConfig.default(),
        )

    @classmethod
    def from_yaml(cls, scoring_path: str | Path) -> "ObservatoryConfig":
        return cls(
            scoring=ScoringConfig.from_yaml(scoring_path),
            paths=PathsConfig.default(),
        )
