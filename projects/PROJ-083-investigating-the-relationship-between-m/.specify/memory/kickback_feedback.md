# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan proposes Poisson Regression for 'Regioisomer Diversity Count'. If the target variable is derived as a count of distinct products and most reactions yield exactly one product (count=1), the data will be heavily zero-inflated or one-inflated. Standard Poisson regression assumes the mean equals the variance; if the variance is near zero (constant target), the model will fail to converge or produce meaningless p-values. The methodology needs a contingency plan (e.g., Zero-Inflated Poisson or treating the target as a binary 'diversity vs. no diversity' classification) if the distribution is degenerate.
