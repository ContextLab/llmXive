# Research: Zero-Shot Drift Detection for AgentDoG 1.5

## Overview

Feasibility research for centroid-based zero-shot drift detection under GitHub Actions free-tier constraints (2 CPU cores, ~7 GB RAM, ≤6 h, no GPU). Confirms models fit CPU/RAM budget, defines the statistical methodology, and documents data acquisition strategy.

## Verified Datasets & Models

No independently re-verified URL list was supplied for this planning round; per the verified-accuracy rule, no URLs are fabricated. Sources below are named as asserted by the spec (which states `agentdog/safety-v1` is "publicly accessible and verified") and by well-known canonical identifiers.

| Component | Identity | Access method | Notes |
| :--- | :--- | :--- | :--- |
| Taxonomy example logs | `agentdog/safety-v1` (Hugging Face dataset) | `datasets.load_dataset("agentdog/safety-v1")` | Spec-mandated; must contain ≥100 labeled examples per category (Safety, Privacy, Bias, Jailbreak). **Verification step in Phase 0**: if the load fails or a category has <100 examples, this is a blocking data-availability gap to surface for scope revision — no substitute dataset is planned. |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | `SentenceTransformer("all-MiniLM-L6-v2")` | ~80 MB, CPU-friendly (Constitution Principle VII). 384-dim embeddings. |
| Baseline model | `google/flan-t5-small` | `AutoModelForSeq2SeqLM` / `AutoTokenizer` | ~300 MB fp32; fits 7 GB RAM on CPU. |
| Novel-log corpus | Public GitHub issue threads | GitHub REST API `GET /repos/{owner}/{repo}/issues` (unauthenticated, seeded repo list, post-2025 filter) | FR-014: ≥500 logs. Real data, PII-scrubbed. |

## Dataset Strategy

| Component | Strategy | Source |
| :--- | :--- | :--- |
| Centroid examples | ≥100 curated logs per category from `agentdog/safety-v1` | HF dataset (canonical id) |
| Scored logs | Full `agentdog/safety-v1` log set + ≥500 GitHub-issue novel corpus | Both real sources above |
| Human annotations | External manual input, `data/human_annotations.json` | Three blinded human annotators; **no public source — code never generates it** |
| Gold standard | Majority vote over 3 annotators ("novel attack" = novel; "known attack"/"benign" = benign) | Derived from human input |

## Model & Methodology

### Embedding Generation
- Model: `all-MiniLM-L6-v2`, **batch size = 64** (verified fact, arXiv:2410.21676, https://arxiv.org/abs/2410.21676).
- CPU-only; embeddings L2-normalized before centroid computation.

### Drift Scoring
- Centroid per category: mean of normalized member embeddings, re-normalized.
- Drift score: cosine distance $D = 1 - \frac{u \cdot c}{\|u\|\|c\|}$ to each centroid; `drift_score = min_C D`, range [0, 2].
- `review_flag = drift_score >= 0.5` (pre-registered operating point, FR-002).

### Statistical Validation (associational framing; no causal claims)
- **Inter-annotator agreement**: mean pairwise Cohen's Kappa over the 3 annotator pairs on the 3-way label; gate κ ≥ 0.6.
- **Separation**: Mann-Whitney U on drift scores, human-novel vs human-benign; p < 0.05, rank-biserial correlation ≥ 0.5. Computed on the FR-017 full-range random sample (≥100 logs) to avoid range restriction.
- **Regression**: logistic regression novel ~ drift_score (scikit-learn + statsmodels-style Wald p-value); report coefficient p-value and AUC-ROC.
- **Bin contrast**: chi-squared test of "novel" proportion, high-drift vs low-drift bins; reject null at α = 0.05.
- **Multiple comparisons**: the family {Mann-Whitney U, logistic coefficient, chi-squared} is reported with Holm-adjusted p-values alongside the pre-registered unadjusted thresholds (numeric family size [deferred] to execution).
- **Power**: sample size is fixed by FR-017 (≥100), not by a power calculation; the report explicitly acknowledges this limitation and gives confidence intervals for all effect sizes.

### Baseline Comparison
- `google/flan-t5-small` zero-shot: prompt "Is this text a novel safety threat not covered by standard categories? Answer yes or no."; score = P(yes). AUC-ROC against human gold standard; baseline validity gate AUC ≥ 0.70 (FR-016). Drift method flagged "computationally efficient alternative" if within 0.10 AUC and latency ≤ 0.5 × baseline. Latency measured per-log on identical CPU hardware, median over repeated runs.

## Compute Feasibility Analysis (CPU-first; no GPU escape hatch needed)

- **RAM**: MiniLM ~80 MB + flan-t5-small ~300 MB + batch-64 activations + streamed data < 2 GB total. Well within 7 GB.
- **Runtime**: embedding ~10k logs at batch 64 on 2 cores ≈ 15–30 min; flan-t5-small inference on the annotated subset (a few hundred logs) ≈ 1–2 h; statistics trivial. Total well under 6 h.
- **GPU**: not required — both models are small CPU-native transformers; no method in this study lacks a faithful CPU form, so no Kaggle offload is planned.

## Decision Rationale

CPU-first throughout: MiniLM and flan-t5-small are deliberately small models that run faithfully on the free-tier runner, satisfying Constitution Principle VII without any GPU dependency. The human-validation hard gate (Principle VI) is preserved: all validity metrics derive exclusively from real three-annotator data; missing human data yields an `Incomplete` status rather than a simulated substitute. `agentdog/safety-v1` is used as mandated by the spec, with a Phase-0 verification step rather than a silent substitution. GitHub-issue acquisition (FR-014) uses the public REST API with a seeded repository list for reproducibility.
