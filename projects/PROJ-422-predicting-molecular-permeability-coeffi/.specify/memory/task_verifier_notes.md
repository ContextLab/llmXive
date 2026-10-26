# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The `code/data/split.py` script fails to run the `execute_split` function because it expects a `config.yaml` at the project root, which is not present, causing unit‑test failures. Consequently the required split files are not reliably produced, and the script’s main path does not enforce the ≤5 percentage‑point stratification constraint. Adding the missing configuration (or removing the hard dependency) and ensuring the stratified split respects the distribution‑difference threshold are needed to satisfy the task.
- **T004** — Requested task execution failed; rerun successfully: run_all.sh exit=1
