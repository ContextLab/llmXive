---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Linguistic Style Matching on Perceived Rapport in Text-Based Communication

**Field**: psychology

## Research question

Does quantifiable Linguistic Style Matching (LSM) in text-based communication correlate with perceived rapport between conversation partners? Specifically, which LSM metrics (pronoun synchronization, function-word alignment, sentence complexity) most strongly predict rapport ratings in online interactions?

## Motivation

Linguistic Style Matching is theorized to facilitate social bonding, yet empirical evidence in digital communication contexts remains limited. This study addresses the gap between theoretical models of linguistic mimicry and measurable outcomes in online text exchanges, providing actionable insights for human-computer interaction design and digital relationship building.

## Related work

- [Mimicry Is Presidential: Linguistic Style Matching in Presidential Debates and Improved Polling Numbers (2015)](http://arxiv.org/abs/1508.01786v1) — Demonstrates LSM effects in high-stakes two-party exchanges, establishing precedent for quantifying style matching in structured dialogues.
- [Exploring Linguistic Style Matching in Online Communities: The Role of Social Context and Conversation Dynamics (2023)](http://arxiv.org/abs/2307.02758v2) — Examines LSM in online communication contexts, highlighting how social dynamics moderate the relationship between linguistic alignment and interaction outcomes.

## Expected results

We expect a positive correlation (r > 0.3) between aggregate LSM scores and rapport ratings, with function-word synchronization showing the strongest predictive power. Medium effect sizes (Cohen's d ≈ 0.5) would support the hypothesis that unconscious linguistic adaptation facilitates perceived connection in digital environments. Statistical significance at p < 0.05 with 95% confidence intervals excluding zero would constitute sufficient evidence.

## Methodology sketch

- Download public dialogue datasets with rapport annotations (e.g., Reddit relationship advice threads, HuggingFace Datasets `conll2003` or OpenML social interaction corpora).
- Preprocess text: clean HTML/markdown, segment into turn-taking units, anonymize user identifiers.
- Compute LSM metrics using LIWC-22 or Linguistic Inquiry Word Count alternative (open-source implementation): pronoun ratios, function-word frequency, sentence length variance.
- Calculate pairwise LSM scores for each conversation pair using the standard LSM formula: 1 - |A - B| / (A + B) for each linguistic feature.
- Extract rapport scores from dataset metadata or use validated proxy measures (e.g., sentiment polarity, interaction continuation, response latency).
- Perform correlation analysis (Pearson/Spearman) between LSM scores and rapport ratings across all conversation pairs.
- Run multiple regression to identify which LSM features (pronouns, function words, complexity) most strongly predict rapport.
- Conduct robustness checks: stratify by conversation length, platform type, and participant demographics.
- Generate visualizations: scatter plots with regression lines, feature importance bar charts, confidence interval plots.
- Reproduce analysis with bootstrap resampling (1000 iterations) to validate stability of effect sizes.

## Duplicate-check

- Reviewed existing ideas: None provided in corpus.
- Closest match: No comparable LSM- rapport studies identified in existing project database.
- Verdict: NOT a duplicate
