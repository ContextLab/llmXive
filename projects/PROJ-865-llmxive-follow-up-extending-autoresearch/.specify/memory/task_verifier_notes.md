# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — declared artifact(s) missing/empty/invalid: data/artifacts/citation_validation_report.json
- **T001** — No directory tree or `.gitkeep` files were presented as evidence; the required project structure (`code/`, `data/`, `data/raw/`, `data/derived/`, `data/artifacts/`, `specs/001-llmxive-followup/contracts/`, `code/01_data_ingestion/`, `code/02_annotation_distillation/`, `code/03_execution/`, `code/04_analysis/`, `code/utils/`, `tests/`) with a `.gitkeep` in each is missing from the provided artifacts. The implementer must create and show this structure.
- **T005** — The implementer did not provide any `.gitignore` file or show that the required lines for `data/raw/`, `data/derived/`, and `data/artifacts/` were added. No artifact was presented, so the task’s requirement is unmet. The next implementer should create or update the root `.gitignore` to include those three directory rules.
- **T006a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011b** — The repository lacks the required input file `data/derived/parsed_traces.json`, the output files `failure_cases.json`, `failure_cases_train.json`, `failure_cases_val.json`, and `failure_cases_test.json`, and the schema file `specs/001-llmxive-followup/contracts/failure_case.schema.yaml`. Moreover, `annotate_failures.py` is truncated and does not contain the full implementation (e.g., the annotation loop, schema validation call, data splitting, and file writing). These missing pieces prevent the task from being considered complete.
- **T013** — The repository lacks the required `data/derived/failure_cases_val.json` input and the generated `data/derived/rules_library.json` output. Moreover, the provided `distill_rules.py` is truncated and does not contain the model‑selection, RAM‑monitoring, coverage‑checking, or LLM‑based rule generation logic mandated by the task. These essential components are missing, so the implementation is not complete.
- **T014** — declared artifact(s) missing/empty/invalid: data/derived/failure_cases_val.json, data/derived/coverage_report.json
- **T015b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T016** — declared artifact(s) missing/empty/invalid: data/artifacts/annotation.log
- **T019a** — The script `code/03_execution/generate_manifest.py` is present but appears truncated and does not contain a complete implementation (e.g., the `write_manifest` function ends abruptly with an unfinished `raise ValueError`). Moreover, the required output file `data/derived/experiment_manifest.csv` does not exist. The task’s core requirement—to generate that manifest CSV—is therefore not satisfied.
