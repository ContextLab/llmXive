# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 11 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- SC‑005 requires extraction precision and recall ≥ 0.9, but the verification steps for T006 only assert `extraction_success_rate >= 0.60` (SC‑001). No test checks precision/recall thresholds, leaving FR‑011’s success criterion unverified.
- SC‑002 mandates reporting the proportion of studies with reference power ≥ 0.8, yet T008’s verification only checks that the disclaimer text is present and PNG files exist. There is no test asserting that the report includes the required reference‑power adequacy metric.
- SC‑008 expects the final audit report to embed the `ExtractionAuditReport` JSON summary. T008’s verification does not confirm that `audit_report.json` contains a reference to the `ExtractionAuditReport` or that the required top‑level keys are present.
- Verification step for T005 references a unit test `tests/unit/test_dataset_metadata_schema.py` which is not present in the repository, so the task cannot be verified as written.
- Task T005 description says it writes `data/processed/filtered_datasets.json`, but other artifacts (plan, data model) refer to `filtered_datasets.csv`. This naming inconsistency makes the deliverable ambiguous and the verification step unclear.
- Task T001 creates directory tree under `projects/PROJ-001‑assessing-statistical-power` instead of the required `projects/PROJ-234‑assessing-statistical-power` as mandated by the specification and constitution (see spec.md and constitution Principle VII). This path mismatch violates the project identifier constraint.
- Task T004 claims to implement robust utilities (api_client with exponential back‑off and DataFetchError) but the underlying `utils/api_client.py` lacks exponential back‑off and does not raise `DataFetchError` on permanent failures, breaking FR‑001/FR‑002 error‑handling requirements.
- Task T005’s ingestion script bypasses the `utils.api_client` wrapper, filters on a non‑existent `url` field, and therefore produces an empty `filtered_datasets.json`. This undermines FR‑001 and FR‑002 (correct OpenML retrieval and filtering) and fails to meet the acceptance criterion that the filtered list be non‑empty.
- The verification step for T005 references a unit test `tests/unit/test_dataset_metadata_schema.py` that does not exist in the repository, making the acceptance criterion untestable and effectively dropped.
- Task T006 lacks any test asserting that extraction precision and recall meet SC‑005 (≥ 0.9). Consequently FR‑011’s success metric (precision/recall thresholds) is not verifiably covered, constituting a weakening of the functional requirement.
- The verification for T001 checks for `.gitkeep` files but does not verify that the top‑level project directory name matches the required `PROJ-234‑assessing-statistical-power` identifier, leaving a constitutional violation unchecked.
