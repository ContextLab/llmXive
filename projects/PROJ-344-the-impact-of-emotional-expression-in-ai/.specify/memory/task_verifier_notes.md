# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — I looked for the required directory tree under `projects/PROJ-344-the-impact-of-emotional-expression-in-ai/` (e.g., `data/raw`, `data/processed`, `data/features`, `code`, `tests/contract`, `tests/unit`, `tests/integration`, `outputs`, `state`) but no such folders or any listing of them were provided. The artifact confirming the project structure is missing.
- **T010** — The required `contracts/dataset_schema.yaml` file is absent, so the test cannot load a real schema. Moreover, the provided `tests/contract/test_dataset_schema.py` is truncated (ends with an unfinished `assert SCH` line) and does not contain a complete validation test. Both the schema artifact and a functional test are missing.
- **T013** — declared artifact(s) missing/empty/invalid: code/extract_facial.py
- **T015** — The `code/compute_metrics.py` file is cut off mid‑implementation (e.g., `lags = np.aran` is incomplete and the metric logic is not fully realized), and the required input file `data/processed/features.csv` is absent. Both the metric implementation and its data source are missing, so the task is not genuinely completed.
- **T016** — declared artifact(s) missing/empty/invalid: code/analyze.py
- **T017** — No code, documentation, or output files were provided that demonstrate the addition of logic to label all results as “associational only” (non‑causal). Without any artifact showing this framing, the requirement is not satisfied. The implementer must supply the modified analysis/reporting scripts or example output where the results are explicitly described as associational.
- **T019** — declared artifact(s) missing/empty/invalid: code/analyze.py
- **T020** — No extraction or regression scripts, no output files (CSV, regression table, or figures) were provided, and there is no evidence of p‑values or pseudo R‑squared values being generated. Consequently the required artifact for User Story 2 is missing.
- **T021** — No code, data files, regression output, or unified analysis report were provided; the claim lacks any tangible artifact demonstrating integration of regression results with consistency scores. The required deliverables (e.g., a report combining US1 consistency scores and regression findings, accompanying CSVs or figures) are missing.
- **T026a** — declared artifact(s) missing/empty/invalid: code/run_pipeline.py
- **T026** — declared artifact(s) missing/empty/invalid: code/run_pipeline.py
