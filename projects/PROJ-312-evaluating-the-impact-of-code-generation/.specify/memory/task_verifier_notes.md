# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002a** — declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt
- **T002b** — declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt
- **T004a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T018b** — declared artifact(s) missing/empty/invalid: data/processed/pr_turnaround.csv
- **T019b** — The repository lacks the required `data/spot_check/annotation_template.csv` file, and the provided `code/validate_spot_check.py` does not contain logic to create that CSV with the specified columns and header comment. The task’s core output is missing.
- **T019c** — The required `data/spot_check/annotations.csv` file is absent, so the script cannot ingest real human annotations. Moreover, the provided `code/validate_spot_check.py` (as shown) contains only loading and sampling utilities and does not compute a false‑negative rate nor generate the expected `validation_report.csv` with that metric. The existing `validation_report.csv` lacks a false‑negative rate column and appears unrelated to the script. The task therefore remains unfinished.
- **T019d** — The only artifact shown is that `data/spot_check/annotations.csv` is missing; there is no code, log output, or final report demonstrating that a CRITICAL warning is logged, the validation status is set to 'UNVALIDATED', or that the analysis proceeds with heuristic‑only classification. These required behaviors are absent, so the task is not satisfied.
- **T038** — No README.md file or its contents were provided in the evidence, so we cannot confirm that documentation was actually updated as required. The implementer must supply the `projects/PROJ-312-evaluating-the-impact-of-code-generation/README.md` file with the expected changes.
- **T039a** — No evidence was provided that the `ruff --fix` command was executed, nor any linting report or modified files showing zero linting errors. The required artifact (a clean codebase or a linting summary) is missing, so the task cannot be confirmed as completed.
- **T039b** — No artifact (e.g., command output, CI log, or report) showing that `black --check` was executed and returned zero formatting errors is present; without such evidence we cannot confirm the requirement was met.
- **T041** — No execution logs, command output, or generated files are provided to show that the commands in `quickstart.md` were run successfully, that each exited with code 0, or that the expected output files were created. The required evidence is missing.
