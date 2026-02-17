# ADR 002: Curation Philosophy

**Status**: Accepted
**Date**: 2026-02-17
**Decision makers**: @4444J99
**Sprint**: LOGOS

## Context

reading-observatory needs a governing philosophy for how material enters and is maintained in its bibliographies and feed lists. The system must balance thoroughness (not missing important sources) with quality (not drowning in noise). It must also define the boundary between what machines do and what humans do in the curation process.

This decision affects every interaction with the repository: how bibliography entries are written, how feeds are selected, how surfaced articles are handled, and what "done" looks like for a curation cycle.

## Decision

**Hybrid curation**: Human-curated bibliographies with machine-assisted feed surfacing.

The division of labor is as follows:

- **Humans decide** what feeds to subscribe to, what bibliography entries to add, what the `relevance` field says, and whether a surfaced article is worth acting on.
- **Machines handle** fetching feeds on schedule, deduplicating items, extracting text, matching keywords, scoring relevance, and presenting a filtered list for human review.

No material enters a bibliography without a human writing its `relevance` field. No feed is added to the subscription list without a human justifying its inclusion. No surfaced article automatically becomes an essay topic; a human must review the surfaced list and decide what to pursue.

The machine layer exists to expand the human's peripheral vision, not to replace the human's judgment.

## Alternatives Considered

### Fully Automated Curation

Subscribe to broad topic feeds, use ML classifiers to categorize incoming articles, automatically add highly-scored items to bibliographies, and generate essay topics without human review.

**Rejected because**:

- Quality degrades without human judgment. Automated classifiers optimize for surface-level relevance (keyword overlap, topic similarity) but cannot assess depth, rigor, originality, or the subtle connections between a source and the system's specific concerns.
- Bibliography entries require a `relevance` field that explains *why* a source matters to the eight-organ system. This requires understanding of the system that no current classifier possesses.
- Automated curation at scale produces a feeling of abundance that masks a poverty of insight. Having 500 automatically-added bibliography entries is less useful than having 50 human-curated entries with meaningful relevance statements.
- The system's value proposition is *curated* reading, not *aggregated* reading. Aggregation is a commodity. Curation is a craft.

### Fully Manual Curation

No feed aggregation. The human operator reads blogs, follows links, attends to serendipitous discovery, and manually adds bibliography entries when something is worth recording.

**Rejected because**:

- Does not scale. The intellectual landscape relevant to the eight-organ system spans multiple disciplines (systems thinking, creative practice, institutional design, AI collaboration). No single person can manually monitor all relevant sources.
- Introduces survivorship bias. The operator will tend to read the same sources repeatedly, missing new voices and emerging conversations.
- Relies on memory and habit rather than systematic process. Important articles encountered during a busy week may be forgotten before they can be recorded.
- The observatory metaphor implies systematic observation, not opportunistic noticing.

### AI-Curated (LLM-Driven)

Use a large language model to read feed items, assess their relevance to the system's themes, write `relevance` fields, suggest bibliography additions, and draft essay topic proposals.

**Rejected because**:

- Premature for the current stage. The system needs to establish its own voice and curatorial standards before delegating judgment to an LLM. If the LLM writes the relevance statements, the bibliographies become a reflection of the LLM's understanding rather than the operator's understanding.
- Cost and complexity. Running LLM inference on every feed item adds API costs and latency that are not justified at current scale.
- Attribution ambiguity. If an LLM writes the `relevance` field, who is the curator? The system's intellectual integrity depends on the human operator engaging with the material, not delegating engagement to a model.
- This alternative may become appropriate in the future, particularly if the system grows to a scale where the human operator cannot review all surfaced items. At that point, an LLM could serve as a first-pass filter, presenting not raw articles but pre-assessed summaries. But that is a future decision, not a current one.

## Principles

The following principles govern curation practice in reading-observatory:

### 1. Relevance Over Comprehensiveness

It is better to have a small bibliography of deeply relevant sources than a large bibliography of loosely related ones. Every entry should pass the test: "If someone asked why this source is in the observatory, could I give a specific answer connected to the eight-organ system?"

### 2. Explanation Over Citation

The `relevance` field is more important than the bibliographic metadata. A perfectly formatted citation with an empty relevance field is less useful than an imperfect citation with a detailed relevance explanation. The observatory exists to explain *why* things matter, not just *what* they are.

### 3. Feeds Are Hypotheses

Adding a feed to the subscription list is a hypothesis: "This source will produce articles relevant to our themes." Hypotheses should be reviewed periodically. Feeds that consistently produce no matches should be removed. Feeds that consistently produce high-quality matches should be noted as particularly valuable. The OPML file is a living document, not an archive.

### 4. Surfacing Is Not Endorsement

An article appearing in `feeds/surfaced.json` means it matched keywords above the threshold. It does not mean it is good, true, or worth reading. The human review step is where quality judgment happens. The machine layer optimizes for recall within the relevant topic space; the human layer optimizes for quality within the recalled set.

### 5. The Loop Must Close

Surfaced articles that are not acted upon within 30 days are archived. This prevents the surfaced list from becoming an ever-growing guilt pile. If an article was not worth pursuing within a month, it is unlikely to become more urgent later. The archive exists for reference, not for obligation.

## Consequences

- Every bibliography entry requires human effort to write the `relevance` field. This limits the rate at which the bibliographies grow, which is intentional.
- The feed aggregation pipeline can run unattended, but its output requires periodic human review. The operator should expect to spend 15-30 minutes per week reviewing surfaced items.
- The system will have false negatives (relevant articles missed because they do not share vocabulary with the tag set). This is accepted as the cost of a conservative matching threshold.
- The system will have false positives (irrelevant articles surfaced because they happen to use relevant keywords). The human review step catches these.
- The curation philosophy may evolve as the system matures. This ADR should be revisited if the scale of monitored feeds exceeds what keyword matching can handle, or if the operator's available time for review decreases significantly.
- Contributors must understand that bibliography PRs will be reviewed for the quality of their `relevance` fields, not just the accuracy of their citations. This raises the bar for contribution but maintains the observatory's value.
