# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan tests the observed residues against the *theoretically biased* expectations (Lebowitz‑Lockard 2021, Pollack & Roy 2024) rather than the uniform null hypothesis stated in the original specification (FR‑003). This mis‑alignment means the analysis will not answer the research question as originally posed – whether the residues are uniformly distributed.
- A chi‑squared goodness‑of‑fit test assumes that the observations are independent draws from the underlying distribution. Here each observation is a deterministic function φ(n) of the integer n, so successive residues are not independent. Using the chi‑squared (or its Monte‑Carlo/Exact fallback) without accounting for this dependence may invalidate the p‑values and the resulting pass/fail decision.
