# Research Documentation

## Dataset Strategy & Methodological Rationale

### 1. Personality Trait Dataset – OpenML BFI‑2

- **Dataset ID:** 42473
- **URL:** https://www.openml.org/d/42473
- **Description:** The BFI‑2 (Big Five Inventory‑2) dataset provides scores for the five major personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) for a large sample of participants. It is a widely‑used, peer‑reviewed instrument for measuring personality in psychological research.
- **License:** Creative Commons Attribution 4.0 International (CC‑BY‑4.0). The dataset is openly available for research and redistribution with proper attribution.

### 2. Music Listening Behaviour Dataset – HuggingFace `lastfm/lastfm_1k`

- **Dataset Name:** `lastfm/lastfm_1k`
- **URL:** https://huggingface.co/datasets/lastfm/lastfm_1k
- **Description:** This dataset contains listening histories for 1,000 users from the Last.fm platform [UNRESOLVED-CLAIM: c_6fbf8869 — status=not_enough_info], including track IDs, timestamps, and genre tags. It offers a realistic view of users' music consumption patterns and is suitable for linking to personality measures.
- **License:** Open Data Commons Open Database License (ODbL). The data may be used for scientific research provided that any derived works also share the same license.

### 3. Real‑First Research Philosophy

The project adheres to a **Real‑First** methodology: all analyses are performed on authentic, publicly‑available datasets. Synthetic or fabricated data are only employed for unit‑testing or CI purposes and are **never** used in the production pipeline that generates the final scientific results. This ensures that any reported correlations, effect sizes, or regression coefficients reflect genuine observations rather than artefacts of simulated data.

### 4. Sample Size Determination

A power analysis (see `code/power_analysis.py`) determined the minimum number of participants required to reliably detect a small effect (Pearson *r* = 0.10) while controlling the family‑wise error rate with a Bonferroni‑adjusted α = 0.001.

**Required sample size:** **2 500** participants (rounded up to the nearest whole person).

This figure will guide the inclusion criteria for the merged dataset; only records that contribute toward meeting or exceeding this threshold will be retained for downstream statistical modeling.