"""Tests for vocabulary building and relevance scoring."""

from src.matcher import build_vocabulary, score_item, score_items


class TestBuildVocabulary:
    def test_merges_tag_sets(self):
        essay_tags = {"governance", "methodology"}
        bib_tags = {"cybernetics", "governance"}
        vocab = build_vocabulary(essay_tags, bib_tags)
        assert "governance" in vocab
        assert "methodology" in vocab
        assert "cybernetics" in vocab

    def test_splits_hyphenated_terms(self):
        vocab = build_vocabulary({"systems-thinking"}, set())
        assert "systems-thinking" in vocab
        assert "systems" in vocab
        assert "thinking" in vocab

    def test_short_parts_excluded(self):
        vocab = build_vocabulary({"ai-ethics"}, set())
        assert "ai-ethics" in vocab
        assert "ethics" in vocab
        assert "ai" not in vocab  # too short (2 chars)

    def test_all_lowercase(self):
        vocab = build_vocabulary({"Governance"}, set())
        assert "governance" in vocab

    def test_empty_inputs(self):
        vocab = build_vocabulary(set(), set())
        assert vocab == set()


class TestScoreItem:
    def test_matching_item(self):
        vocab = {"systems", "thinking", "systems-thinking", "governance"}
        item = {
            "title": "Systems Thinking in Practice",
            "summary": "How governance shapes systems thinking approaches.",
        }
        result = score_item(item, vocab, {})
        assert result["score"] > 0
        assert "systems" in result["matched_terms"]
        assert "thinking" in result["matched_terms"]
        assert "governance" in result["matched_terms"]

    def test_non_matching_item(self):
        vocab = {"cybernetics", "governance"}
        item = {
            "title": "Best Pasta Recipes",
            "summary": "Delicious Italian cooking for beginners.",
        }
        result = score_item(item, vocab, {})
        assert result["score"] == 0.0
        assert result["matched_terms"] == []

    def test_collection_boost(self):
        vocab = {"systems", "thinking", "governance", "cybernetics", "feedback",
                 "emergence", "complexity", "autopoiesis", "design", "architecture"}
        coll_tags = {"systems-thinking": {"systems", "thinking"}}
        item = {
            "title": "Systems Thinking Article",
            "summary": "About thinking in systems.",
            "collection": "systems-thinking",
        }
        boosted = score_item(item, vocab, coll_tags)
        unboosted = score_item(item, vocab, {})
        assert boosted["score"] > unboosted["score"]

    def test_empty_vocabulary(self):
        result = score_item({"title": "Test", "summary": "Test"}, set(), {})
        assert result["score"] == 0.0

    def test_score_capped_at_one(self):
        # Create a scenario where boost could push score > 1.0
        vocab = {"a"}
        coll_tags = {"test": {"aaa", "bbb", "ccc", "ddd", "eee", "fff", "ggg", "hhh", "iii", "jjj"}}
        item = {
            "title": "aaa bbb ccc ddd eee fff ggg hhh iii jjj",
            "summary": "aaa bbb ccc",
            "collection": "test",
        }
        result = score_item(item, vocab, coll_tags)
        assert result["score"] <= 1.0


class TestScoreItems:
    def test_filters_below_threshold(self):
        vocab = {"systems", "thinking", "governance", "cybernetics"}
        items = [
            {"title": "Systems Thinking Governance", "summary": "Cybernetics."},
            {"title": "Cooking Recipes", "summary": "Pasta and salad."},
        ]
        scored = score_items(items, vocab, {}, min_score=0.1)
        assert len(scored) == 1
        assert scored[0]["title"] == "Systems Thinking Governance"

    def test_sorted_by_score_descending(self):
        vocab = {"systems", "thinking", "governance", "cybernetics", "feedback"}
        items = [
            {"title": "Governance", "summary": "About governance."},
            {"title": "Systems Thinking Governance", "summary": "Cybernetics and feedback."},
        ]
        scored = score_items(items, vocab, {}, min_score=0.01)
        assert len(scored) == 2
        assert scored[0]["relevance_score"] >= scored[1]["relevance_score"]

    def test_includes_metadata_fields(self):
        vocab = {"governance"}
        items = [{"title": "Governance Post", "summary": "About governance."}]
        scored = score_items(items, vocab, {}, min_score=0.01)
        assert "relevance_score" in scored[0]
        assert "matched_terms" in scored[0]
        assert "matched_collections" in scored[0]
