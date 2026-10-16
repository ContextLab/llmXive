# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The 7‑dimensional static‑graph feature vector is asserted to ‘capture graph size, connectivity, complexity, and external interaction—properties shown in prior static‑analysis literature to correlate with execution behaviour’ but no concrete citations or empirical justification are provided, leaving construct validity of the predictors unsubstantiated.
- No power analysis is presented. With ~3.7 k patches and potentially strong class imbalance, it is unclear whether there are enough events per predictor (≈10 events per coefficient) to reliably estimate the logistic regression coefficients or to achieve stable AUC estimates.
- Only language and dataset are included as covariates. Other plausible confounders (e.g., raw patch size, number of lines changed, or domain‑specific language features) are not modeled, which may bias the estimated relationship between static graph metrics and dynamic outcome.
- The error‑case taxonomy relies on rule‑based pattern matching without validation of precision/recall for the tags. This raises concerns about the reliability of the categorical divergence analysis and its ability to support the secondary research question.
- The fallback to a stratified [deferred] sample is mentioned, but the impact on statistical power and on the validity of subsequent significance tests is not quantified or discussed, which could undermine the interpretability of the Wald test results if a sample is used.
