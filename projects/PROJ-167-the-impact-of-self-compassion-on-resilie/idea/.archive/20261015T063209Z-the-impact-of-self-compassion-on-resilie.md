---
field: psychology
submitter: agent:flesh_out
---

# How Does Negative Peer Feedback Shape Contributor Persistence in Online Knowledge Communities?

**Field**: psychology

## Research question

Does the tone of automated or peer feedback received on an edit (reverted with an explanatory message vs. reverted without one) predict whether a newcomer to Wikipedia continues contributing, and does the effect differ by the newcomer's initial contribution intensity?

## Motivation

Online knowledge communities depend on retaining new contributors, yet a large fraction of newcomers quit after their first edit is undone. Psychological theory on feedback framing suggests that rejection accompanied by an explanation may preserve a sense of competence and belonging, while unexplained rejection may be read as personal dismissal. Whether the *presence of an explanation* in real-world moderation actions causally predicts persistence has not been quantified at scale, and the answer bears directly on how communities design moderation workflows.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv with two search strategies: (1) a focused query combining "reverted edits," "newcomer retention," and "Wikipedia moderation feedback"; and (2) a broadened query on "negative feedback persistence online communities emotion regulation self-compassion." The focused query returned primarily computer-science work on vandalism detection rather than on the psychological effect of feedback tone on persistence; the broadened query returned two papers on self-compassion measurement, summarized below.

### What is known

- [Effects of a Co-Regulation Model for MR Teacher Training: HRV and Self-Compassion as Indicators of Emotion Regulation (2025)](https://arxiv.org/abs/2502.15383) — Establishes that emotion-regulation responses to evaluative feedback are measurable constructs, motivating the study of feedback-induced disengagement.
- [Multimodal Detection of Higher-Order Behavioral Constructs: Self-Compassion in Structured Reflective Interaction (2026)](https://arxiv.org/abs/2609.37148) — Demonstrates that higher-order psychological responses to setbacks can be detected from behavioral traces rather than self-report alone.

### What is NOT known

No published work has quantified whether the presence versus absence of an explanatory message attached to a revert predicts newcomer persistence in Wikipedia, nor whether this effect is moderated by the newcomer's initial contribution intensity. Existing Wikipedia retention studies focus on revert *rate* rather than feedback *tone*, and emotion-regulation research on feedback has not been connected to large-scale behavioral trace data.

### Why this gap matters

Community moderators and platform designers currently lack evidence about whether writing a short explanation when undoing an edit is worth the effort. A quantified effect size would inform moderation training, automated-assistant design (e.g., semi-automated revert tools that prompt for explanations), and theory on belonging cues in online communities.

### How this project addresses the gap

The methodology below extracts revert events with and without explanatory edit summaries from public Wikipedia edit-history dumps, links them to newcomer persistence outcomes measured from the same public logs but at a later time window, and estimates the tone–persistence association with a mixed-effects model — producing exactly the large-scale behavioral evidence the gap describes.

## Expected results

We expect newcomers whose first reverted edit includes an explanatory edit summary to have a higher probability of making a subsequent edit within 30 days than those reverted without explanation, with the effect strongest for low-intensity newcomers. A null result would indicate that explanation presence does not matter once revert rate and newcomer activity are controlled, which would itself be an actionable finding for moderation practice. Evidence standard: a mixed-effects odds ratio with bootstrap 95% CI excluding (or clearly including) 1.0, robust to alternative persistence windows (14/60 days).

## Methodology sketch

- **Data acquisition**: download a public Wikimedia edit-history slice for two mid-size Wikipedia language editions (e.g., `simplewiki` and `dewiki` full-history dumps from `https://dumps.wikimedia.org/`, each < 5 GB decompressed for simplewiki; use the `.sql.gz` stub-meta-history` or the `metahistory7zdump` for a bounded time range 2018–2022).
- **Cohort definition**: identify newcomers = accounts whose first-ever edit falls in the observation window; retain those whose first edit was reverted within 24 hours (revert detection via the standard `mwreverts` algorithm on parent-ID chains, available as a Python package).
- **Predictor (feedback tone)**: from the reverting edit's summary string, classify as "explained" (non-empty, non-boilerplate summary) vs. "unexplained" (empty or pure template tag). This is a property of the *moderator's* action, measured independently of the newcomer's own behavior.
- **Outcome (persistence)**: whether the newcomer makes ≥1 further edit within 30 days of the revert, and the count of edits in 90 days, computed from the same dump but a strictly later time window (distinct measurement occasion from the predictor).
- **Moderator**: newcomer initial intensity (number of edits in the 7 days before the revert).
- **Statistical analysis**: logistic mixed-effects model `persisted ~ explained_revert + initial_intensity + explained_revert:initial_intensity + (1|article) + (1|reverter)` via `statsmodels`; Wald test on the interaction, 1,000-resample bootstrap CI.
- **Robustness checks**: alternative windows (14/60 days), drop reverts by bots (identified via bot flag), permutation test shuffling explanation labels within reverter, sensitivity to restricting to human reverters only.
- **Compute budget**: stream-parse dumps line-by-line (no full in-memory load; chunked `bz2` reading), ≤ 4 GB RAM, < 3 hours on a 2-core GitHub Actions runner; outputs a coefficient table, persistence curves, and a reproducible notebook.

## Duplicate-check

- Reviewed existing ideas: the-impact-of-self-compassion-on-resilie.md (rejected, out of scope).
- Closest match: the rejected self-compassion buffering study; both concern responses to negative feedback, but this project examines a different construct (feedback tone vs. self-compassion language), different data (Wikipedia edit history vs. Amazon reviews), and a different outcome (behavioral persistence vs. subsequent star rating).
- Verdict: **NOT a duplicate**.
