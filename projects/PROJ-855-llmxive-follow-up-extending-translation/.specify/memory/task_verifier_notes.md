# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — The repository lacks the required `config.yaml` file, so thresholds cannot be loaded, and the provided `generate_data.py` snippet does not show any concrete labeling logic that uses those thresholds. Without the configuration file (and evidence of the labeling implementation), the task is not genuinely fulfilled.
- **T016** — declared artifact(s) missing/empty/invalid: data/raw/synthetic_episodes.parquet, data/checksums.json
- **T016b** — declared artifact(s) missing/empty/invalid: data/raw/synthetic_episodes.parquet, data/processed/train.parquet, data/processed/test.parquet
- **T016c** — The required output files `data/processed/train.parquet` and `data/processed/test.parquet` are not present, indicating that the geometry‑disjoint split was not actually performed and saved. Consequently the task’s core requirement is unmet.
- **T018** — The repository lacks a `config.yaml` file, so custom thresholds cannot be read, and the provided `generate_data.py` excerpt does not show any new function that re‑labels the raw `synthetic_episodes.parquet` and re‑runs the geometry‑disjoint split logic as required. Both the necessary configuration source and the specific re‑labeling/split function are missing.
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/trained_model.pt
- **T025** — The implementer did not provide any model summary output or any file showing the total parameter count. No artifact demonstrating that the model has fewer than 10,000,000 parameters before saving is present, so the task requirement is not satisfied.
- **T027b** — The repository contains a `code/train_baseline.py` file, but it is truncated and does not include any training loop or model‑saving logic, and the required output file `data/processed/baseline_model.pt` is absent. Consequently the baseline model is neither trained nor persisted, so the task’s requirement is not met.
