# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan uses the RBF‑Morph “doe.csv” proxy dataset, which lacks the required processing‑parameter columns (laser power, scan speed, layer thickness) and the target mechanical‑property columns (yield strength, ductility). This violates construct validity: the measured variables do not match the constructs defined in the specification (FR‑001, SC‑001‑SC‑004).
- Confounding variables (e.g., alloy composition, microstructural state) are not addressed. The plan only checks collinearity among x1‑x3, but does not implement any strategy to detect or control for latent confounds that could drive spurious associations.
- The plan states it will “download a verified open dataset (RBF‑Morph “doe.csv”)” and proceeds to model the relationship between processing parameters and mechanical properties. However, the RBF‑Morph dataset only provides three generic numeric predictors (x1, x2, x3) and a generic response column, none of which correspond to the required AM‑specific variables (laser power, scan speed, layer thickness, yield strength, ductility) defined in FR‑001. Using this proxy dataset does not satisfy the functional requirement to study AM alloy process‑property correlations, making the dataset inappropriate for the research question.
