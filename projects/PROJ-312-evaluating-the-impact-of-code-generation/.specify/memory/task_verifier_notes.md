# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required `projects/PROJ-312-evaluating-the-impact-of-code-generation/{code,data,tests,contracts,artifacts,state}` directory tree is present; the implementer did not supply any filesystem listing or screenshots confirming the directories exist. The task remains undone until the specified folder hierarchy is created and verified.
- **T002a** — declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt
- **T002b** — declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt
- **T002c** — No `requirements.lock` file is presented at `projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.lock`, nor any content showing the result of `pip freeze`. The required lock file is missing, so the task is not satisfied.
- **T003** — declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/pyproject.toml
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No evidence was provided showing that the required directories (`data/raw/`, `data/processed/`, `data/spot_check/`, `artifacts/`, `tests/`) actually exist in the repository; the claim is unsubstantiated. The implementer must create and show these directories (non‑empty or at least present) to satisfy the task.
- **T012a** — declared artifact(s) missing/empty/invalid: data/raw/repos.json
- **T012c** — The required `data/processed/pr_turnaround.csv` was not created (the partial file was left unchanged), `data_quality_warning.log` is missing, and `truncated_repos.txt` was not updated with any repo names. No merge or promotion of the partial data was performed, so the task’s output artifacts are absent.
- **T014** — The repository does not contain the required `data/processed/excluded_repos.txt` file, and the provided excerpt of `code/fetch_data.py` does not show any logic that checks `MIN_PR_THRESHOLD` or writes skipped repository names to that file. Consequently the task’s core requirement is not met.
- **T019b** — The repository contains a partially‑implemented `code/validate_spot_check.py` that stops before actually writing the CSV template, and the required `data/spot_check/annotation_template.csv` file is absent. Consequently the script does not generate the requested template with the specified columns and header comment.
- **T019d** — declared artifact(s) missing/empty/invalid: data/spot_check/annotations.csv
- **T019d#1** — declared artifact(s) missing/empty/invalid: data/spot_check/validation_status.json
- **T019e** — The required `annotations.csv` is missing, yet the provided `validation_report.csv` contains no false‑negative rate nor any indication of a critical warning or a validation status of 'UNVALIDATED'. The task’s strict fallback behavior is not demonstrated.
