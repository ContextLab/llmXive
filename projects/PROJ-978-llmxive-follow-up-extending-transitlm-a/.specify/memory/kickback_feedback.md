# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: data/graph_utils.py, data/raw/transitlm_ground_truth.json, data/processed/graph_validation_report.json, data/processed/adjacency_graph.pkl
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: models/baseline.py
- `T014` (rejected 1x): The required files `data/analysis/route_complexity_metrics.json` and `data/analysis/raw_inflection_data.json` are absent, so the implementation cannot have produced the requested output or performed the analysis. The missing artifacts must be created for the task to be considered complete.
- `T009` (rejected 1x): No `config.py` file or its contents are present in the provided evidence; therefore the required environment configuration, random seed handling, and city‑mapping constants have not been implemented. The task remains undone.
- `T010` (rejected 1x): The provided `tests/contract/test_preprocess_schema.py` is truncated and does not contain any actual test logic invoking `data/preprocess.py`. Moreover, the required `data/preprocess.py` file is missing entirely, so the contract test cannot verify the output schema as specified. The missing module and incomplete test file must be added/fixed.
- `T017` (rejected 1x): The provided `performance_report.json` contains the required summary fields, but the prerequisite input file `data/analysis/raw_inflection_data.json` is missing and there is no evidence of a JSON‑formatted `logs/evaluation.log` with the required fields (`route_id`, `predicted_station`, `validity_score`, `risk_flag`). Both the logging artifact and the input data are required for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

