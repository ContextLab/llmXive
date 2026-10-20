# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan adopts `logP` (a calculated hydrophobicity descriptor) as a proxy target for molecular permeability because no open dataset contains experimental permeability coefficients. Using `logP` as the target does not directly address the research question of predicting *permeability* coefficients and may introduce systematic bias, violating FR‑001 which requires ingestion of *permeability* datasets. This constitutes a wrong‑dataset‑for‑the‑question issue.
- All listed verified datasets (e.g., ChEMBL‑derived RDKit descriptors, Half‑ChEMBL, SMILES‑Transformers) provide only SMILES and descriptor columns; none include experimental permeability measurements. Relying on these datasets without true permeability values undermines the validity of the comparative evaluation between GNN and RF models for the intended property.
