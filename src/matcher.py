"""Vocabulary building and TF-IDF relevance scoring.

Builds a keyword vocabulary from essay tags and bibliography tags,
then scores feed items by matching title+summary text against the vocabulary.
Uses simple term frequency — no external ML dependencies (ADR-001).
"""

import re


def build_vocabulary(essay_tags: set[str], bib_tags: set[str]) -> set[str]:
    """Build keyword vocabulary from essay and bibliography tags.

    Splits hyphenated terms to include both the compound and parts:
    'systems-thinking' → {'systems', 'thinking', 'systems-thinking'}
    """
    all_tags = essay_tags | bib_tags
    vocabulary = set()
    for tag in all_tags:
        vocabulary.add(tag.lower())
        if "-" in tag:
            for part in tag.split("-"):
                if len(part) > 2:
                    vocabulary.add(part.lower())
    return vocabulary


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words and hyphenated compounds."""
    text = text.lower()
    # Extract hyphenated compounds first
    tokens = re.findall(r"[a-z]+-[a-z]+(?:-[a-z]+)*", text)
    # Then individual words
    tokens.extend(re.findall(r"[a-z]{3,}", text))
    return tokens


def score_item(
    item: dict,
    vocabulary: set[str],
    collection_tags: dict[str, set[str]],
) -> dict:
    """Score a single feed item against the vocabulary.

    Returns {score, matched_terms, matched_collections}.
    Score is matched terms / vocabulary size, boosted for collection-specific matches.
    """
    if not vocabulary:
        return {"score": 0.0, "matched_terms": [], "matched_collections": []}

    text = f"{item.get('title', '')} {item.get('summary', '')}"
    tokens = set(_tokenize(text))

    matched = vocabulary & tokens
    base_score = len(matched) / len(vocabulary) if vocabulary else 0.0

    # Boost for collection-specific matches
    item_collection = item.get("collection", "")
    matched_collections = []
    boost = 0.0
    for coll_name, coll_tags in collection_tags.items():
        coll_matches = coll_tags & tokens
        if coll_matches:
            matched_collections.append(coll_name)
            if coll_name == item_collection:
                boost += 0.1 * len(coll_matches)

    score = min(base_score + boost, 1.0)

    return {
        "score": round(score, 4),
        "matched_terms": sorted(matched),
        "matched_collections": sorted(matched_collections),
    }


def score_items(
    items: list[dict],
    vocabulary: set[str],
    collection_tags: dict[str, set[str]],
    min_score: float = 0.3,
) -> list[dict]:
    """Score all items and return those above min_score, sorted by score descending."""
    scored = []
    for item in items:
        result = score_item(item, vocabulary, collection_tags)
        if result["score"] >= min_score:
            scored.append(
                {
                    **item,
                    "relevance_score": result["score"],
                    "matched_terms": result["matched_terms"],
                    "matched_collections": result["matched_collections"],
                }
            )
    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored
