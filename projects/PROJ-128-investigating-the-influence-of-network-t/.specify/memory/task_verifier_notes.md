# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided that the required directories (`code/`, `data/`, `contracts/`, `tests/`) actually exist or contain any files; the response contains only the task description and specifications, not the claimed project structure. The implementer must create and show these directories (with at least placeholder files) to satisfy the requirement.
- **T011** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T019** — The required output files `data/processed/structural_metrics.csv` and `data/processed/dynamic_metrics.csv` are absent, and the referenced schema `contracts/output.schema.yaml` (or `schema.yaml`) does not exist. Consequently the batch processing logic cannot be verified as producing the correct aggregated CSVs per the task specification.
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- **T028** — No code, test, or documentation artifact was provided showing that the pipeline now checks for zero significant findings after FDR correction and adds an explicit statement to the report. The required implementation and verification evidence are missing.
- **T035** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T040** — No evidence of updated files in `docs/` or modifications to `README.md` was provided; the claim lacks any actual documentation artifacts to verify.
- **T041** — No code artifacts, diff logs, or documentation were provided to demonstrate that any cleanup or refactoring was performed, nor any evidence that GPU calls were removed. Without tangible files or test results, the claim cannot be verified.
- **T042** — No evidence of a `quickstart.md` validation run, logs, or reproducibility output is present; the required artifact confirming that the full pipeline was executed and validated is missing.
- **T043** — No review document or report was provided; the implementer did not supply any artifact demonstrating a final review of the reports for associational language compliance. The required compliance review output is missing.
