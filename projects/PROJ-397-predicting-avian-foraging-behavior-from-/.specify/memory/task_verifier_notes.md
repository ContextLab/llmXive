# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008a** — The required script `data/download_guild_source.py` does not exist, so no code reads the manual CSV, raises `FileNotFoundError`, or creates `data/raw/guild_source.csv`. Consequently the core functionality mandated by the task is missing.
- **T008b** — declared artifact(s) missing/empty/invalid: data/generate_guild_mapping.py, data/raw/guild_source.csv, data/processed/guild_mapping.csv
- **T039b** — declared artifact(s) missing/empty/invalid: data/calculate_100m_buffers.py
- **T039c** — declared artifact(s) missing/empty/invalid: data/join_guild_labels.py
- **T039d** — declared artifact(s) missing/empty/invalid: data/write_merged_observations.py, data/processed/merged_observations.csv
- **T010** — The `tests/test_data_contract.py` file exists but the required schema file `contracts/dataset.schema.yaml` is missing, causing the test to fail at load time. Moreover, the provided test code is truncated and does not clearly assert that `merged_observations.csv` contains the specific columns (`species_id`, `foraging_guild`, and all 100 m land‑cover proportion columns). The missing schema and incomplete test logic must be added for the task to be satisfied.
- **T040** — The required `data/aggregate.py` file does not exist in the repository, so no implementation, output CSV, or logging behavior can be verified. The task’s core artifact is missing, making the requirement unmet.
- **T041** — declared artifact(s) missing/empty/invalid: models/train.py, data/models/random_forest.pkl, data/models/training_metrics.json, data/models/cv_predictions.json
- **T059** — declared artifact(s) missing/empty/invalid: models/stratified_permutation.py, data/models/null_distribution.npy
