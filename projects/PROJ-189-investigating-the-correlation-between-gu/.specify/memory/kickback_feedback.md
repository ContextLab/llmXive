# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The correlation analysis computes Spearman correlations between each genus and cognitive_score without adjusting for known confounders (age, sex, BMI, education). This risks attributing associations to microbes that are actually driven by these covariates.
- The Random Forest model is described as using microbial taxa only; there is no explicit inclusion of demographic covariates (age, sex, BMI). Omitted variable bias may inflate predictive performance and obscure true relationships.
- The plan sets a hard overlap threshold of 500 samples and emits a warning if N < 100, but it does not perform a formal power analysis for the multiple‑testing burden of genus‑level correlations or for the regression model, leaving uncertainty about whether the sample size is sufficient to detect meaningful effects.
- The plan states that AGP data is fetched from an “official Qiita‑derived HuggingFace mirror”. Constitution Principle VI requires microbiome taxonomic tables to be obtained directly from the American Gut Project via the Qiita/EBI repository, not via a third‑party mirror. Using a mirror may violate provenance requirements and could be considered an inappropriate dataset source.
- The results.schema.yaml contract requires `checksum_agp` and `checksum_hrs` fields in the `dataset.metadata` section of `unified_results.json`, but the plan’s Unified Results Assembly description does not mention adding these checksum fields to the assembled JSON. This creates a mismatch between the plan and the contract specification.
- The plan computes Variance Inflation Factors (VIF) on the CLR‑transformed genus matrix (Task T003). Because CLR transformation imposes a linear constraint (the transformed values sum to zero), the feature set is inherently collinear, making VIF undefined or artificially inflated. Using VIF to flag collinearity after CLR is methodologically invalid and will always flag many taxa as problematic.
