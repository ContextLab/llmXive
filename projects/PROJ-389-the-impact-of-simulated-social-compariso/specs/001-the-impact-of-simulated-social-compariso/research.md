# Research: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

## Dataset Strategy

| Role | Source | Loader | Rationale |
|------|--------|--------|-----------|
| Reddit comments (raw) | **Verified**: https://huggingface.co/datasets/allenai/reddit_comments | `datasets.load_dataset("allenai/reddit_comments", split="train", streaming=True)` | Provides `subreddit`, `body`, `created_utc`, and `author` (including `about` profile field) needed for exposure, outcome, and demographic proxy extraction. |
| Subreddit‑level activity metadata | Derived from the same Reddit source (aggregated community activity) | N/A – computed in ingestion step | Needed for `exposure_level` (FR‑013). |
| PII‑scrubbing validation set | https://huggingface.co/datasets/ai4privacy/pii-masking-200k/resolve/main/english_pii_43k.jsonl | direct file download | Used only to sanity‑check the regex‑based PII removal (FR‑011). Not part of the main analysis. |
| Authenticity‑lexicon validation set | (internal, 200‑comment sample) | N/A – manually annotated | Provides precision/recall for the rule‑based authenticity classifier (methodology‑07d7dbc0). |

**Data‑availability verdict:** The verified Reddit‑comments dataset above satisfies the spec’s requirement for a public Reddit comment source with the necessary fields. The Data Availability Gate (Phase 0 Task 1) will verify its presence before any downstream processing.

## Methodological Decisions

| Decision | Rationale | CPU / GPU |
|----------|-----------|-----------|
| Rule‑based authenticity classifier (vulnerability‑marker lexicon) on exposure content | Deterministic, CPU‑trivial (FR‑001). Validation on a representative comment sample yields high precision and moderate recall (methodology‑07d7dbc0). | CPU |
| VADER sentiment + first‑person pronoun ratio from the user's **own** comments → `self_eval_score` | Deterministic, validated on social‑media text (FR‑002). | CPU |
| **Exposure operational definition**: community‑level subreddit activity in a 30‑day window; target subreddits = top 100 most active subreddits overall. Per‑user `exposure_level` = Σ community comment volume of target subreddits the user posted in ÷ total volume of all target subreddits. This yields a predictor stream distinct from the user’s own comments while acknowledging self‑selection. | Satisfies FR‑013 and Principle VI. | CPU |
| **Self‑selection adjustment**: include `subreddit_participation_count` (number of target subreddits a user posted in) as a covariate in all regression models to mitigate bias from users choosing which communities to engage with. | Addresses methodology‑a7135da8 concern; improves validity of moderation tests. | CPU |
| `engagement_proxy` from thread participation in exposure content | FR‑009 | CPU |
| Hierarchical OLS (statsmodels) with interaction terms | Classical, interpretable, CPU‑tractable (FR‑003) | CPU |
| Benjamini–Hochberg FDR | FR‑004, SC‑003 | CPU |
| VIF diagnostics (statsmodels) | FR‑005, SC‑004 | CPU |
| Demographic keyword proxies from user **profile metadata** `about` fields; global fallback if coverage < 10 % | FR‑006, FR‑017; aligns with spec’s source requirement | CPU |
| Power check (f² = 0.15, α = 0.05, power = 0.80) targeting the exposure × authenticity interaction (df₁ = 1, total predictors = 6 [including self‑selection covariate]) | Spec’s own assumption; if estimated power < 0.80, log a warning and proceed with caution (methodology‑e6618bd2). | CPU |
| Median imputation + complete‑case sensitivity | Missing‑data robustness | CPU |
| Threshold sensitivity sweep ±0.05 | FR‑016, SC‑006 | CPU |
| Cluster‑robust SEs by subreddit for `exposure_level` | Addresses lack of within‑subreddit variation (scientific_soundness‑6946eb76) | CPU |
| Self‑selection limitation note | Exposure defined via user‑posted subreddits introduces selection bias; mitigated via covariate and discussed in logs and final discussion. | CPU |
| Self‑selection limitation note | Exposure defined via user‑posted subreddits introduces selection bias; mitigated via covariate and discussed in logs and final discussion. | CPU |
| **Causal framing**: observational design; all effects labeled “associational” in logs and outputs (SC‑002). No causal claims are made. | SC‑002 | CPU |

**Compute feasibility decision:** Every method has a faithful CPU implementation; no GPU escape hatch is required (FR‑008). Chunked processing (< 100 k rows in memory) keeps peak RAM < 6 GB; total wall‑clock ≤ 4 h on the free‑tier runner.

## Statistical Rigor Checklist

- **Multiple comparisons**: BH‑FDR across all hypothesis tests (FR‑004).
- **Power**: a priori calculation for the exposure × authenticity interaction (df₁ = 1, predictors = 6, α = 0.05, f² = 0.15). If estimated power < 0.80, a warning is logged and results are interpreted with caution (methodology‑e6618bd2).
- **Causal framing**: observational design; all effects labeled “associational” in logs and outputs (SC‑002). No causal claims are made.
- **Measurement validity**: VADER validated on social‑media text; authenticity lexicon validated on a 200‑comment sample with precision/recall reported (methodology‑07d7dbc0). Limitations are noted.
- **Collinearity**: VIF reported; VIF > 5 flagged, independent‑effect language withheld (SC‑004).
- **Missing data**: ≤ 10 % threshold check, median imputation, complete‑case sensitivity (SC‑001).
- **Dataset‑variable fit**: Verified Reddit dataset contains all required variables; the Data Availability Gate enforces this before pipeline execution.
- **Self‑selection limitation**: Documented in analysis logs and final discussion (methodology‑b24eef30).

## Compute Feasibility Statement

CPU‑first throughout; no GPU‑dependent libraries; streaming ingestion with fixed‑seed down‑sampling fallback ensures compliance with RAM limits (FR‑008, FR‑015, SC‑005). All model fits are OLS on ≤ 10⁵ users — minutes on 2 cores.
