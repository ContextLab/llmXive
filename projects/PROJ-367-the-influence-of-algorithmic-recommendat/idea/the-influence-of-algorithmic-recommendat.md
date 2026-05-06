---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Field**: psychology

## Research question

How do personalized recommendation algorithms affect the balance between exploration and exploitation in learner behavior on online education platforms?

## Motivation

Online learning platforms increasingly rely on recommendation algorithms optimized for engagement and completion, yet their downstream effects on intellectual curiosity remain unstudied. This question addresses a gap between algorithmic design goals (maximize time-on-platform) and educational outcomes (broad skill development). Understanding this dynamic would inform policy and design choices for platforms serving millions of learners.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex using queries: (1) "recommendation algorithm online learning exploration exploitation" and (2) "algorithmic curation learner behavior diversity." Retrieved 4 papers total; most results focused on reinforcement learning agents or social dilemma tasks rather than human learner behavior on educational platforms.

### What is known

- [Improved cooperation by balancing exploration and exploitation in intertemporal social dilemma tasks (2021)](http://arxiv.org/abs/2111.09152v1) — Establishes that exploration-exploitation tradeoffs operate in human decision-making contexts, though not specifically in online learning environments.

### What is NOT known

No published work has measured how recommendation system exposure quantitatively affects topic diversity in learner course selections. There is no evidence on whether algorithmic curation reduces exploration relative to baseline or control conditions on actual educational platforms.

### Why this gap matters

Platform designers need empirical evidence to balance engagement metrics with educational breadth. If recommendations systematically narrow learning paths, this could have downstream effects on workforce skill diversity and individual intellectual development.

### How this project addresses the gap

This project will analyze public enrollment datasets to compare topic diversity between users with different levels of recommendation exposure, directly quantifying the exploration-exploitation shift that prior work has only theorized.

## Expected results

We expect to observe a negative correlation between recommendation intensity and course topic diversity. A statistically significant effect (p<0.05, Cohen's d>0.3) on diversity metrics would confirm algorithmic narrowing; a null result would suggest learner agency overrides algorithmic influence. Either outcome would be publishable as it constrains current assumptions about recommendation system effects.

## Methodology sketch

- Download public course enrollment datasets from OpenML (e.g., "MOOC Dataset" or "Online Course Completion" repositories) or Zenodo educational data portals.
- Extract user-level course sequences with categorical course tags (subject, level, institution).
- Compute topic diversity metrics: Shannon entropy of course category distribution, Gini coefficient of category engagement.
- Estimate recommendation exposure from available metadata (e.g., "recommended" flag, click-through patterns, or time since enrollment).
- Stratify users into high/low recommendation exposure groups based on exposure percentile.
- Perform two-sample t-test comparing mean diversity scores between exposure groups.
- Run robustness checks: permutation test for group assignment, control for enrollment time and platform.
- Visualize results with boxplots of diversity by exposure group and regression of diversity on continuous exposure measure.
- Document all data sources with DOIs/URLs in reproducible code repository.

## Duplicate-check

- Reviewed existing ideas: [N/A — no existing fleshed-out ideas in corpus]
- Closest match: [None]
- Verdict: NOT a duplicate
