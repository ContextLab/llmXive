# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows all required directories except `logs/` are present; the `logs/` directory is missing entirely, so the hierarchy is not complete as specified.
- **T002** — The `code/requirements.txt` file is present and correctly pins exact versions for all six packages, and `code/__init__.py` exists, but there is no provided evidence (e.g., CI logs or command output) showing that `pip install -r code/requirements.txt` actually succeeded without warnings. Without this execution proof, the task’s verification condition is unmet.
- **T003** — Requested task execution failed; rerun successfully: code/lint.sh exit=1
