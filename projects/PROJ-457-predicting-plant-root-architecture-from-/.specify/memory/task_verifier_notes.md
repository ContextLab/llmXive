# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003b** — No linting output or report files are provided; there is no evidence that `black --check code/` and `flake8 code/` were run or that they produced zero errors. The required artifact (a linting verification result) is missing.
- **T014a** — No `artifacts/state.json` file was presented or described, and there is no evidence that such a file exists or contains valid JSON. The required artifact is missing, so the task is not satisfied.
- **T014b** — No `artifacts/state.json` file was presented, and there is no evidence that the `p_n_available` flag was written to it. The required artifact is missing, so the task is not satisfied.
- **T014c** — No evidence of a `logs/deviation.log` entry recording “Hypothesis Unverifiable” nor a `artifacts/state.json` file with the required flag is provided; the required artifacts are missing.
- **T015h** — No `logs/deviation.log` file or its contents were provided, so we cannot verify that the required log entry `"FR-003: KNN imputation excluded to preserve statistical validity; missing nutrients are excluded"` exists. The implementer must supply the log file with the exact entry.
- **T015d** — No artifact (e.g., script output, log file, or filtered dataset) was provided showing the count of species and rows excluded when applying the n ≥ 20 filter, so the requirement cannot be verified. The implementer must supply the actual filtering code/run results and the corresponding log entries.
- **T015e** — declared artifact(s) missing/empty/invalid: reports/species_counts.json
- **T015i** — No evidence of a `logs/deviation.log` file was provided, nor any excerpt showing entries for FR-002 and FR-003. Without the actual log file contents, we cannot confirm that the required deviations have been recorded. The implementer must supply the log file with the appropriate entries.
- **T015** — The provided `code/data_ingestion.py` only contains helper functions for detecting the data source column, filtering by that column, and (partially) filtering rows with missing nutrients; it does not implement the required species‑count filtering (n < 20) nor does it generate the `artifacts/reports/species_counts.json` file (the file is missing). Additionally, the file ends abruptly (`retu…`) indicating the implementation is incomplete. The task’s core requirements are therefore not satisfied.
- **T035c** — declared artifact(s) missing/empty/invalid: reports/metrics.json
- **T035a** — declared artifact(s) missing/empty/invalid: reports/metrics.json
- **T035b** — declared artifact(s) missing/empty/invalid: reports/metrics.json, reports/species_counts.json
- **T020** — The repository lacks the required `contracts/model_results.schema.yaml` file, and the provided `tests/contract/test_schemas.py` snippet does not show the specific `test_model_metrics_schema_validates_fields` function that validates that schema. Both the schema definition and the concrete test are missing, so the task is not satisfied.
- **T026b** — No code, log file, or other artifact was provided that reads F‑test p‑values, checks they lie in [0, 1], and writes the required “F-test verification passed/failed” message. Without such evidence the task’s requirement is not demonstrated.
- **T028a** — No `artifacts/literature_ranges.json` file or verification script is present, and there are no cited literature sources. The required output and evidence are missing, so the task is not satisfied.
- **T029c** — declared artifact(s) missing/empty/invalid: reports/model_metrics.json
