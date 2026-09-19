# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan defines 'unphysical' trajectories as those leaving the attractor for $\sigma > 0.1$ and excludes them. This introduces a selection bias: the analysis of bias $\Delta \lambda$ will only be performed on trajectories that *remain* on the attractor. If high noise systematically pushes trajectories off the attractor, the remaining sample is a biased subset (survivorship bias). The methodology must account for this by either modeling the probability of escape as a function of $\sigma$ or explicitly stating that the bias analysis is conditional on 'bounded trajectories only', which limits the generalizability of the claim to 'observable' chaos.
- The plan mentions 'Bonferroni correction or FDR control' for multiple comparisons. However, the primary analysis is a regression (Δλ ~ f(σ, N)). Regression does not typically require Bonferroni correction for the coefficients unless testing multiple specific hypotheses about individual coefficients. The plan conflates 'multiple comparisons' (e.g., testing each noise level individually) with 'regression modeling'. If the goal is regression, the p-values for coefficients are the primary output; if the goal is pairwise testing, then correction is needed. The plan is ambiguous on whether the regression is the primary test or a post-hoc fit, leading to potential statistical misinterpretation.
