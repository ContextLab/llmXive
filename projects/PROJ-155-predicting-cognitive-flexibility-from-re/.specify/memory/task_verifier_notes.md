# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The directory layout, requirements.txt, .ruff.toml, and plan.md updates are present and linting passes, but `code/config.py` does not define the required `FD_threshold=0.2` parameter (it only includes `snr_threshold` and `batch_size`). Add the missing `FD_threshold` entry to satisfy the task.
- **T002** — Requested task execution failed; rerun successfully: tests/test_contracts.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
