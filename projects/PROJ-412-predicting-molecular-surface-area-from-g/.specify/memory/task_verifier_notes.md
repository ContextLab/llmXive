# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003a** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T015a** — The required output files `data/processed/conformer_params.json`, `data/processed/failure_report.csv`, `data/processed/conformers.parquet` (and the state file `conformer_state.json`) are absent from the repository, so the conformer generation and logging steps have not been realized. The implementation in `code/data/preprocess.py` does not contain code that creates these artifacts.
