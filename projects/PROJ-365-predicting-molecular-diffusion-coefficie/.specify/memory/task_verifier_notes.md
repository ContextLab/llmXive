# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The provided `code/utils/logging.py` is truncated and the `log_invalid_smiles` function is unfinished, so the required tag `[ERROR_SMILES]` cannot be logged. Additionally, the expected `data/logs/ingestion.log` file does not exist, indicating the logger has not yet written any output. The task therefore remains incomplete.
- **T005a** — The provided `tests/unit/test_logging_tags.py` is truncated (ends with `log_missi`), does not contain the full test logic, and never processes a mixed‑validity CSV. Moreover, the required `data/logs/ingestion.log` file is missing, so the test cannot verify the presence of the tags. The task’s requirement is therefore not satisfied.
- **T006c** — The required output file `artifacts/reports/runtime_memory.json` does not exist, so the total runtime is not being recorded as specified. The implementer must create the JSON file with the `"total_seconds"` key containing the measured runtime.
- **T006e** — No `monitor.py` file or modified version is presented, and there is no JSON report showing a `"peak_memory_mb"` field. Without the actual code change or output artifact, the requirement to extend `monitor.py` cannot be verified as fulfilled.
- **T007b** — No ingestion script, featurized JSONL output, training script, model files, or evaluation report are present. The claim provides only a textual description of the intended functionality, but the required artifacts (code, data files, and result metrics) are missing, so the task is not satisfied.
- **T012** — The provided `code/ingestion/ingest.py` is cut off mid‑function (the `record` dict is unfinished and the file ends abruptly), so the script does not actually implement the full pipeline or write any output. Moreover, the required output file `data/processed/featurized.jsonl` is absent. Both the implementation and the expected artifact are missing/incomplete.
- **T015** — declared artifact(s) missing/empty/invalid: tests/contract/test_featurization.py, schema.yaml
- **T021** — declared artifact(s) missing/empty/invalid: reports/evaluation.json
- **T027** — declared artifact(s) missing/empty/invalid: reports/sensitivity_summary.md
- **T027b** — declared artifact(s) missing/empty/invalid: tests/contract/test_sensitivity_stability.py
- **T035** — declared artifact(s) missing/empty/invalid: reports/resource_summary.json
- **T036** — declared artifact(s) missing/empty/invalid: tests/contract/test_resource_report.py
