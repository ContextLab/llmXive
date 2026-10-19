# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007a** — the task writes platform-owned path(s) inside the project: `state/artifact_hashes.json` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T015a** — Checked the `data/checkpoints/fetch_checkpoint.json` file (present) and the pytest log `code/.tasks/T015a.code_tests_test_fetch_checkpoint.py.log`, which shows both checkpoint‑creation and resumption tests failing because the script aborts with “No games specified in config.yaml” and never writes a checkpoint file. The required integration and resume behavior are not demonstrated.
- **T002** — Requested task execution failed; rerun successfully: code/scripts/preprocess.py exit=1
- **T014** — The evidence collector shows no artifacts for this task — no `run_records.csv` with a `competitive_pressure` column, no helper from T033b, and no execution output or spot-check calculations were provided. Without the actual CSV (or a sample of it) showing non-negative integer `competitive_pressure` values that match a manual lagged-pressure calculation, the claim cannot be verified.
- **T015b** — Requested task execution failed; rerun successfully: code/scripts/preprocess.py exit=1
