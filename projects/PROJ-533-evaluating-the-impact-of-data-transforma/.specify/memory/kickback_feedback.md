# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan applies mean imputation for near‑symmetric variables and median imputation for skewed variables (≤10 % missing). Imputation can alter distributional shape and therefore affect both Type I error and power estimates, yet the design does not control for this potential confound (e.g., by conducting a sensitivity analysis of imputation impact).
- The dual null‑simulation strategy mentions both stratified label shuffling *and* residual permutation, but the plan does not specify how the two estimates will be combined or compared. Without a clear aggregation rule, the resulting Type I error estimate may be ambiguous or double‑counted, threatening causal interpretation of the simulation results.
- SC‑004 requires bootstrap confidence‑interval half‑width ≤ 0.02, yet the plan’s power analysis justification assumes ≥ 45 datasets provide > 80 % power for the Friedman test. Given the realistic possibility of ending with fewer than 50 usable datasets (especially after strict filtering), the half‑width target may be unattainable, making the precision requirement potentially unrealistic and the inference under‑powered.
- The listed verified datasets (e.g., `unsplash_urls`, `reddit_syac_test`, `malicious_urls_train`, `bounded_null`) are URL‑list or hash datasets that lack continuous numeric variables and categorical group labels required for t‑test/ANOVA analysis, making them inappropriate for the research question.
- FR‑001 requires downloading **at least 50 public datasets**. The plan currently cites only seven verified datasets, and the fallback to synthetic data does not satisfy the “public dataset” clause, leaving the requirement unmet.
- The plan uses *residual permutation* as one of the dual null‑simulation strategies for estimating Type I error of t‑tests/ANOVA. Residual permutation assumes exchangeability of model residuals and is typically appropriate for regression‑type statistics, not for simple two‑sample t‑tests or one‑way ANOVA on transformed data. Applying it here may yield biased Type I error estimates, making the validation of transformation effects methodologically unsound.
