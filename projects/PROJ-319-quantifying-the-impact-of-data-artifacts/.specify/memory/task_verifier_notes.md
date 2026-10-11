# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a4** — The unit test `test_create_logs_dir` failed because the expected `logs/` directory was not found at the project root, even though `create_logs_dir.py` printed a success message. The script’s behavior does not actually create the required `logs/` directory in the correct location, so the task’s requirement is not satisfied.
- **T001b** — Checked for a `.gitignore` file at the project root; the evidence list shows directories (`data/`, etc.) but no `.gitignore` artifact and no content confirming the required exclusion patterns. The required file is missing or does not contain the specified entries.
- **T046a** — Requested task execution failed; rerun successfully: code/main.py exit=1
