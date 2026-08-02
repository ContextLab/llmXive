# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018** — The provided `src/main.py` imports the validation utilities but never actually calls them, and the script ends before saving a validated dataset to `data/processed/games.parquet`. Moreover, the expected `games.parquet` file is absent from the repository. The task’s requirement—to run schema validation on the generated dataset and then write the validated data to the specified Parquet file—is therefore not fulfilled.
- **T027** — declared artifact(s) missing/empty/invalid: data/results/model_metrics.json, schema.yaml
