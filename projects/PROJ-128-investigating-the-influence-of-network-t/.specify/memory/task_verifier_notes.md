# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided that the required directories (`code/`, `data/`, `contracts/`, `tests/`) actually exist or contain any files; the response contains only the task description and specifications, not the claimed project structure. The implementer must create and show these directories (with at least placeholder files) to satisfy the requirement.
- **T011** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The required artifact `tests/unit/test_structural.py` does not exist in the repository, so no unit test for `code/preprocess/structural.py` is provided. The task remains unfinished.
- **T019** — The repository lacks the required output files `data/processed/structural_metrics.csv` and `data/processed/dynamic_metrics.csv`, and the referenced schema `contracts/output.schema.yaml` is missing. Moreover, `code/main.py` is truncated and does not contain the batch‑processing logic needed to aggregate metrics and write those CSVs. The task’s core requirements are therefore not satisfied.
- **T020** — declared artifact(s) missing/empty/invalid: data/logs/exclusion_log.json
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- **T028** — No code, test, or documentation artifact was provided showing that the pipeline now checks for zero significant findings after FDR correction and adds an explicit statement to the report. The required implementation and verification evidence are missing.
- **T035** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T040** — No evidence of updated files in `docs/` or modifications to `README.md` was provided; the claim lacks any actual documentation artifacts to verify.
