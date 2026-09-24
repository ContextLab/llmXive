# Dataset Strategy & Methodological Rationale

## Real‑First Principle

In this project we adhere to a **Real‑First** data strategy: all analyses are performed on authentic, publicly‑available datasets. Synthetic data are generated **only** for unit‑testing or CI purposes and are never used in the production pipeline or reported results. This ensures that our findings about the relationship between musical preference and personality traits are grounded in real‑world observations and respect the licensing terms of the source datasets.

## Datasets

### 1. OpenML BFI‑2 (Big Five Inventory)
- **Dataset ID:** 42473
- **URL:** https://www.openml.org/d/42473
- **Description:** The BFI‑2 provides validated self‑report scores for the five major personality dimensions (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) for a large cohort of participants.
- **License:** Creative Commons Attribution 4.0 International (CC BY‑4.0). The license permits redistribution, adaptation, and commercial use provided appropriate credit is given to the original authors.

### 2. HuggingFace `lastfm/lastfm_1k`
- **URL:** https://huggingface.co/datasets/lastfm/lastfm_1k
- **Description:** This dataset contains listening histories for 1,000 Last.fm users [UNRESOLVED-CLAIM: c_7efed1d9 — status=not_enough_info], including track‑level metadata and genre tags. It is commonly used for music‑recommendation research and offers a realistic view of users' genre preferences.
- **License:** Creative Commons Attribution‑NonCommercial 4.0 International (CC BY‑NC‑4.0). The dataset may be used for non‑commercial research with proper attribution.

## Methodological Rationale

The combination of **OpenML BFI‑2** and **Last.fm 1k** provides a complementary view of participants:
- **Personality traits** (from BFI‑2) give a robust psychological profile.
- **Listening behavior** (from Last.fm) supplies quantitative measures of musical preference across standardized genre categories.

By merging these sources on the shared `user_id` field, we obtain a unified dataframe that links personality scores with genre‑level listening minutes, enabling correlation and regression analyses that directly address our research question.

## Sample Size Requirement

A power analysis (detecting a Pearson correlation of **r = 0.10** with a Bonferroni‑adjusted significance level **α = 0.001** and target power **0.80**) indicates that a minimum of **1,712** participants are required to achieve adequate statistical power. This figure was computed using the standard normal approximation for correlation tests:

\[
N = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^{2}}{r^{2}} + 3
\]

where \(Z_{1-\alpha/2} = 3.291\) (for α = 0.001) and \(Z_{1-\beta} = 0.842\) (for power = 0.80). The resulting required sample size is **1,712** individuals. This requirement will be compared against the actual overlap size of the two datasets during data ingestion; if the overlap is insufficient, the study will be flagged for under‑power.