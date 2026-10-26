# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The specification (FR‑008) requires a linear regression analysis with heteroscedasticity‑robust standard errors for each topology‑performance pair, yet the plan only describes Spearman correlation, partial correlation, and permutation testing. Absence of the mandated regression step means the analysis will not satisfy the spec’s regression reporting requirement.
- The plan states an a‑priori power analysis targeting ≥ 60 % power to detect ρ = 0.3, but later computes a Minimum Detectable Effect Size (MDES) for 80 % power. This inconsistency creates ambiguity about which power target governs the exploratory flag and may lead to contradictory conclusions about study feasibility.
- Phase 4 – Primary Statistical Analysis claims “Spearman Correlation … (FR‑004)”. FR‑004 in the specification is defined as *Robustness Checks*, not the correlation requirement. The correct functional requirement for correlation is not explicitly numbered; the plan should reference the appropriate FR (e.g., FR‑004 is incorrect) or remove the FR tag.
- Phase 5 – Robustness Checks & Window Comparison writes a `window_comparison.csv` file, but no contract for this artifact exists in `contracts/`. All generated data artifacts should have a corresponding schema contract (e.g., a `window_comparison.schema.yaml`).
