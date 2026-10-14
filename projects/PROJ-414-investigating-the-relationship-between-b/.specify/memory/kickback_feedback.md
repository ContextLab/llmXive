# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The primary skill proxy is ‘years of training’ or the binary task condition (Improvisation vs. Scripted). Neither directly measures improvisational skill quality (e.g., expert rating, melodic novelty). This weak construct validity threatens the core hypothesis that network dynamics relate to *musical improvisation skill*.
- Power analysis shows only ~46 % power to detect a medium effect (d = 0.5) with N≈20 at α = 0.05. This is well below conventional thresholds (≥ 0.80) and makes a null result likely, undermining the ability to draw reliable conclusions.
- Confound control includes age, motion, scanner, and session, but omits other plausible covariates (instrument type, musical genre, practice intensity, education level) that can influence both network dynamics and training years, leaving residual confounding.
- The plan states it will acquire an open‑source fMRI dataset that includes improvisation vs. scripted task labels, but cites the HuggingFace parquet `clane9/openneuro-fslr64k`. This public parquet is a generic OpenNeuro preprocessing benchmark and does **not** contain the required musical improvisation task labels (Improv/Scripted) nor the behavioral variables (years of training) required for the hypothesis. The dataset therefore does not match the scientific question, violating FR‑001 and the Constitution’s requirement for appropriate data. Replace it with a verified OpenNeuro dataset that actually includes improvisation tasks (e.g., ds000246, ds001600) or provide evidence that the cited parquet contains the necessary columns.
- The plan states that significance will be assessed with **5 000 permutations** (see line 30), but the specification (spec.md, FR-005) requires **1000 permutations**. This discrepancy violates the functional requirement and must be reconciled.
- Principle I of the constitution requires a designated Single Source of Truth (SSoT) artifact. The plan’s Constitution Check table does not name any specific file (e.g., a manifest or master CSV) as the SSoT, which leaves the project without an explicit reference point for figures/tables.
