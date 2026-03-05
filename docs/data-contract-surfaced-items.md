# Surfaced Items Data Contract

Version: `1.0`  
Last updated: `2026-03-05`

## Producer / Consumers
- Producer: `reading-observatory` (`feeds/surfaced.json`)
- Consumer: `essay-pipeline` (`src.topic_suggester`)
- Consumer (publish target): `public-process` data snapshots

## Canonical Schema
Each surfaced item is a JSON object with these fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | yes | Human-readable article title |
| `url` | string | yes | Absolute canonical URL |
| `summary` | string | no | Feed summary / excerpt |
| `published` | string | no | ISO datetime when source published |
| `collection` | string | no | Primary subscription collection |
| `feed_title` | string | no | Feed display name |
| `relevance_score` | number [0,1] | yes | Matching score from `matcher.score_items` |
| `matched_terms` | string[] | no | Vocabulary terms that matched |
| `matched_collections` | string[] | no | Collections with positive matches |
| `surfaced_date` | string (`YYYY-MM-DD`) | yes | Date item was surfaced by pipeline |

## Compatibility Rules
- Canonical scoring key is `relevance_score`.
- `essay-pipeline` accepts both `relevance_score` and legacy `score` for compatibility.
- If both are present, `score` takes precedence in the consumer.
- `surfaced_date` is accepted by consumers as a recency signal and normalized internally.

## Validation Guidance
- Producer-side tests must assert `relevance_score` is emitted.
- Consumer-side tests must assert both key variants are accepted.
- Any schema change must update this document and both repos in one PR set.
