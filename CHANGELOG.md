# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-02-24

### Added
- Full implementation of feed aggregation pipeline (src/aggregator.py)
- Bibliography loading, validation, and tag extraction (src/bibliographies.py)
- OPML parsing, RSS/Atom feed fetching, and deduplication (src/feeds.py)
- TF-IDF keyword matching and relevance scoring (src/matcher.py)
- Configuration management with YAML loading (src/config.py)
- 4 curated bibliography collections (17 entries): systems-thinking, creative-practice, institutional-design, ai-human-collaboration
- OPML feed subscription file with 13 curated feeds across 4 collection groups
- Scoring configuration (config/scoring.yaml)
- 67 tests across 5 test modules with full fixture suite
- CI workflow with ruff linting, pytest, and bibliography validation
- Weekly feed aggregation scheduled workflow (Monday 06:00 UTC)
- CLI: `python -m src.aggregator [--dry-run]` and `python -m src.bibliographies --validate`

### Changed
- seed.yaml: implementation_status SKELETON → CANDIDATE
- Replaced minimal CI with full CI (ruff + pytest + bibliography validation)

## [0.1.0] - 2026-02-17

### Added
- Initial repository structure
- README with full portfolio-quality documentation
- seed.yaml automation contract
- CI workflow (minimal validation)
- ADR 001: Initial architecture decisions (YAML, OPML, Python, keyword matching)
- ADR 002: Curation philosophy (hybrid human + machine approach)
- MIT License

[Unreleased]: https://github.com/organvm-v-logos/reading-observatory/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/organvm-v-logos/reading-observatory/releases/tag/v0.1.0
