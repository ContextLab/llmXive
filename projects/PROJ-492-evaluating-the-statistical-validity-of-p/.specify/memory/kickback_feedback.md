# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan does not provide a statistical power or sample‑size justification for estimating the overall inconsistency prevalence in the real‑world corpus. Without a margin‑of‑error calculation, it is unclear whether the ≤5 000 URL target yields a precise enough estimate to satisfy the research question.
- Potential confounding due to source heterogeneity (e.g., blogs vs. corporate reports) and clustering by source is only mentioned as “if non‑trivial” and lacks a concrete adjustment strategy. This may bias the binomial test of overall inconsistency proportion.
- The extraction approach relies on a limited set of XPath/CSS selectors and a fallback regex, but the plan does not describe validation of selector coverage across diverse page layouts. Incomplete extraction could systematically miss certain metrics, threatening construct validity of the audit.
- Constitution Principle VI requires that any discrepancy greater than an absolute 0.05 be flagged. The plan’s FR‑004 tolerance uses `max(0.01, 0.2 × reconstructed_p)` (and a 5 % effect‑size tolerance), which can permit discrepancies larger than 0.05 (e.g., for reconstructed p = 0.8 the allowed difference is 0.16). This conflicts with the constitution’s stricter absolute‑difference rule.
- Constitution VI requires flagging any discrepancy greater than an absolute 0.05, yet FR‑004 implements a relative tolerance `max(0.01, 0.2 × reconstructed_p)`. This allows discrepancies >0.05 to be considered consistent when the reconstructed p‑value is large (e.g., p=0.30 → tolerance 0.06). The validation rule therefore conflicts with the non‑negotiable principle and may miss genuine inconsistencies, undermining the scientific claim of exhaustive detection.
