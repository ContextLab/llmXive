# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan mentions “Testing: `pytest` with contract validation via `jsonschema`” but does not specify which contracts are validated, nor the filenames that will be checked (e.g., importance results, metrics, runtime). Explicitly mapping plan steps to each contract would improve traceability.
- The plan states that the pipeline will “record reproducibility metadata in `manifest.json`”, yet the `manifest.schema.yaml` contract is not listed among the contracts exercised, nor is the manifest generation step detailed (e.g., which fields are populated). This omission may cause a mismatch with the contract schema.
