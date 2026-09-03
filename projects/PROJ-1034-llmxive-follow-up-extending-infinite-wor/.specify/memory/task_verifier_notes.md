# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016b** — The provided `run_simulation.py` does not read `config/default.yaml`, runs only the user‑specified number of steps (default 100) and lacks any check for a minimum of 10,000 steps. It also never flags a “Time‑Bound Baseline” nor writes a Parquet file to `data/raw/baseline_partial.parquet`. Moreover, the required `config/default.yaml` and the expected output Parquet file are missing from the repository.
- **T057** — declared artifact(s) missing/empty/invalid: src/analysis/validate_metrics.py, data/raw/baseline_partial.parquet
