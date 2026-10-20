# Research: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

## Dataset Strategy
| Role | Source | Loader | Rationale |
|------|--------|--------|-----------|
| Reddit comments (raw) | Pushshift Reddit dump (public) – accessed via HuggingFace `datasets` streaming endpoint | `datasets.load_dataset("pushshift/reddit", split="comments", streaming=True)` | Open, programmatic, no auth, contains timestamps, subreddits, text needed for all features. |
| Subreddit metadata (popularity) | Pushshift subreddit statistics (public) – accessed via `datasets.load_dataset("pushshift/reddit", name="submissions", streaming=True)` (filter for subreddit aggregates) | `datasets.load_dataset("pushshift/reddit", name="submissions", streaming=True)` | Provides **subreddit‑wide comment counts** used as the exposure proxy, ensuring a distinct predictor stream from the outcome. |
| VIF benchmark (optional sanity check) | `https://huggingface.co/datasets/shim0114/VIF-Bench/resolve/main/labels/vi_conflicts.jsonl` | `datasets.load_dataset("shim0114/VIF-Bench", split="train")` | Provides example VIF calculations for validation of our own VIF implementation. |
| No gated datasets required; all data sources are openly downloadable. |

## Methodological Decisions
| Decision | Rationale | CPU / GPU |
|----------|-----------|-----------|
| **Feature extraction** – rule‑based authenticity classifier + spaCy POS tagging for pronouns, NLTK VADER for sentiment. | Deterministic, lightweight, fully CPU‑compatible (FR‑001, FR‑002). | CPU |
| **Exposure proxy** – **subreddit‑wide exposure proxy**: weighted average of subreddit comment volume for subreddits a user posts in (derived from the subreddit metadata source, not from the user’s own comments). | Satisfies distinct‑stream principle (VI) and provides a plausible exposure measure. | CPU |
| **Regression** – OLS hierarchical models via `statsmodels`. | Classical statistics, interpretable, runs comfortably on 2‑core CPU. | CPU |
| **Multiple‑comparison correction** – Benjamini‑Hochberg FDR (FR‑004). | Controls false discovery rate when testing multiple interaction terms. | CPU |
| **Collinearity diagnostics** – VIF using `statsmodels.stats.outliers_influence.variance_inflation_factor`. | Ensures predictors are not overly redundant (FR‑005). | CPU |
| **Additional covariates** – total comment count, subreddit popularity score, month of activity, baseline sentiment. | Controls for major confounders not captured by primary predictors (addresses methodology‑4e1e7c28). | CPU |
| **Demographic extraction** – keyword‑based inference from comment text (age/gender markers). | Uses only data present in the comment dump; if coverage <10 % falls back to global analysis (addresses data_resources‑76a00e9c). | CPU |
| **Power analysis** – a priori calculation (f² = 0.15, α = 0.05, power = 0.80) → N≈400 per subgroup; require N≥500 for robust detection, otherwise log limitation (methodology‑19fcf0e1). | Guarantees sufficient sample size for interaction tests. | CPU |
| **Missing data handling** – median imputation for any residual missingness; complete‑case sensitivity check (methodology‑dc3a607e). | Prevents bias from missing values. | CPU |
| **Validation of constructs** – manual annotation of a random representative sample for authenticity cues and self‑evaluation; compute inter‑rater reliability (Cohen’s κ) and report (methodology‑0be7a213). | Provides empirical grounding for the proxy metrics. | CPU |
| **Visualization** – Matplotlib/Seaborn interaction plots. | Generates publication‑ready figures on CPU. | CPU |
| **Sensitivity analysis** – threshold sweep ±0.05 (10 runs). | Demonstrates robustness of moderation effects (FR‑016). | CPU |
| **Memory management** – streaming ingestion, on‑the‑fly aggregation, optional fixed‑seed random down‑sampling to ≤ 6 GB RAM (FR‑015). | Guarantees CI runner feasibility. | CPU |

No GPU‑only methods are required; the entire pipeline is CPU‑first.

## Statistical Rigor Checklist
- **Multiple comparisons**: Benjamini‑Hochberg FDR applied (FR‑004).  
- **Power / Sample size**: Target N ≥ 500 per subgroup; if not met, log power‑limitation warning (SC‑005).  
- **Causal framing**: All effects labeled “associational” (SC‑002).  
- **Measurement validity**: Sentiment via VADER (validated on social media); authenticity via rule‑based vulnerability markers, validated against manually annotated sample (see Validation of constructs).  
- **Collinearity**: VIF ≤ 5 → acceptable; otherwise flag (SC‑004).  
- **Missing data**: Median imputation + complete‑case sensitivity (addressed).  

## Compute Feasibility Statement
The pipeline processes the Reddit stream in chunks (< 100 k rows at a time), keeping peak RAM ≤ 5 GB. All model fits complete in ≤ 30 minutes on the GitHub Actions runner. Total wall‑clock time estimated ≤ 4 hours, well under the 6‑hour limit.

---

