# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories (`code/src/`, `code/tests/`, `data/raw/`, `data/processed/`, `results/`) and files (`requirements.txt`, `README.md`) are present, but there is no provided evidence of a `git status` (or equivalent) showing these items as untracked, which is part of the task’s verification criteria. Provide the git status output (or equivalent proof) confirming the directories are untracked.
- **T002** — The provided `requirements.txt` contains the required pinned packages, but there is no evidence that `pip install -r requirements.txt` was run in a fresh virtual environment or that `pip freeze` was captured to confirm the installed versions match the pins. Execution logs or freeze output are needed to verify the task’s installation requirement.
- **T004** — Requested task execution failed; rerun successfully: code/src/feasibility_gate.py exit=1
