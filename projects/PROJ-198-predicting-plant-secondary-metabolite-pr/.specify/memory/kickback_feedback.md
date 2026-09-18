# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T030a ('retrain_with_thresholds') is unexecutable because it claims to sweep BGC detection thresholds while loading cached PCA features from `data/interim/pca_features.csv`. The PCA features are derived from the BGC count matrix generated in T014. If T014 is not re-run with new thresholds, the input features remain static, making the 'sweep' mathematically impossible. The task must explicitly re-run T014 (antiSMASH parsing) for each threshold value before applying PCA or modeling.
- T030a states: 're-run ONLY the BGC parsing step (T014) with varied... thresholds' while loading cached PCA features from `data/interim/pca_features.csv`. This violates FR-007 and SC-002. The sensitivity analysis requires sweeping the *detection* threshold to regenerate the BGC feature matrix (counts/presence). Loading pre-cached PCA features (which are derived from a fixed BGC matrix) makes the sweep mathem impossible; the feature matrix would not change, rendering the sensitivity analysis invalid.
