# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listing or other evidence was provided to show that the required folders (`projects/PROJ-227-assessing-the-trade-offs-between-static-/data/raw/`, `data/processed/`, `state/`, `code/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`) actually exist. The implementer must supply an `ls -R` (or equivalent) output confirming the full directory tree.
- **T001b** — No `.gitignore` file content or location is provided, and there is no output showing `git check-ignore` confirming the specified paths are ignored. The required artifact is missing, so the task is not satisfied.
- **T002a** — No evidence of a Python 3.11 virtual environment was provided (no `.venv` directory, activation script, or command output showing `python --version`), so the required artifact is missing. The implementer must create the virtualenv in the specified path and supply verification that activation yields Python 3.11.x.
- **T002b** — The required file `projects/PROJ-227-assessing-the-trade-offs-between-static-/requirements.txt` is missing, and no evidence is provided that `pip install -r requirements.txt` runs successfully. The existing `requirements.txt` in the repository root does not satisfy the specified path requirement.
- **T004** — The required file at `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/config.yaml` is missing, and no evidence of the Python type‑checking verification is provided. The existing `code/config.yaml` does not satisfy the specified path requirement.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: data/logs/pipeline.log
- **T009** — The required `state/projects/PROJ-227-assessing-the-trade-offs-between-static-.yaml` file does not exist, and there is no evidence that `code/hash_artifacts.py` was executed to populate a `tool_versions` block. Without the YAML file containing version strings and timestamps, the task’s requirement is unmet.
