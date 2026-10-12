# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories, `requirements.txt`, `.ruff.toml`, `code/config.py`, and the updated `plan.md` are present and correct, but the verification test `test_ruff_linting_passes` failed because the `ruff` module is not available (`No module named ruff`). The task explicitly demands that `ruff check .` pass, so the linting step is not satisfied. Install `ruff` (or add it to the environment) and ensure the codebase passes linting to complete the task.
