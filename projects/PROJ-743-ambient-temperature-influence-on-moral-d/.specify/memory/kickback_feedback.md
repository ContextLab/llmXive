# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan writes a `cleaned_dataset.parquet` file (step 5) but the data‑model only defines a `merged_dataset.parquet` artifact and provides a schema for it. No schema or entity definition exists for `cleaned_dataset.parquet`, creating a mismatch between the plan and the data‑model.
- The Constitution Check claims the Single Source of Truth is `data/processed/cleaned_dataset.parquet`, yet the data‑model designates `data/processed/merged_dataset.parquet` as the processed dataset. This inconsistency violates Constitution Principle I, which requires a single, unambiguous SSoT.
- The `contracts/moral_temperature.schema.yaml` contract is listed in the repository but the plan never references it nor produces an artifact that conforms to this schema. Every contract must be exercised by at least one plan element; the omission leaves the contract unvalidated.
