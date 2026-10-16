# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `scripts/setup_manifest.txt` and `scripts/setup.sh` (both present) and the execution log `code/.tasks/T001.scripts_setup.sh.log` showing the script runs and creates the listed directories. However the automated test `tests/test_setup_script.py` failed with a PermissionError, indicating the script is not executable in the test environment, so the verification that `setup.sh` creates the directories is not reliably satisfied. The permission issue must be fixed (e.g., ensure the script is marked executable before the test runs).
- **T002b** — The provided log (`code/.tasks/T002b.code_check_requirements.py.log`) reports a warning that the pip dry‑run output did not contain the required “Successfully installed …” text, and no evidence of a successful, conflict‑free install is supplied. The task’s verification condition is therefore unmet.
- **T003a** — Checked the project root (`projects/PROJ-349-predicting-the-impact-of-ball-milling-on`) for a `.flake8` configuration file but no such file was found, nor any evidence showing its contents include `max-line-length = 88`. The required linting configuration artifact is missing.
- **T003b** — Requested task execution failed; rerun successfully: code/scripts/check_black.sh exit=127
- **T004** — Requested task execution failed; rerun successfully: code/scripts/init_git_repo.py exit=1
