# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listing or other evidence was provided to show that the required folders (`projects/PROJ-227-assessing-the-trade-offs-between-static-/data/raw/`, `data/processed/`, `state/`, `code/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`) actually exist. The implementer must supply an `ls -R` (or equivalent) output confirming the full directory tree.
- **T001b** — No `.gitignore` file content or location is provided, and there is no output showing `git check-ignore` confirming the specified paths are ignored. The required artifact is missing, so the task is not satisfied.
- **T002a** — No evidence of a Python 3.11 virtual environment was provided (no `.venv` directory, activation script, or command output showing `python --version`), so the required artifact is missing. The implementer must create the virtualenv in the specified path and supply verification that activation yields Python 3.11.x.
- **T002b** — The required file `projects/PROJ-227-assessing-the-trade-offs-between-static-/requirements.txt` does not exist, and no evidence is provided that `pip install -r requirements.txt` (pointing to that file) succeeds. The present `requirements.txt` in the repository root is irrelevant to the specified path.
- **T004** — The required file at `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/config.yaml` is missing, and no evidence of the Python type‑checking verification is provided. The existing `code/config.yaml` does not satisfy the specified path requirement.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: data/logs/pipeline.log
- **T011** — The repository contains a `download.py` script but the expected output file `data/raw/humaneval.json` is absent, and there is no `state/checksums.json` showing a recorded checksum. Consequently the required dataset file, record count verification, and checksum logging are not present.
