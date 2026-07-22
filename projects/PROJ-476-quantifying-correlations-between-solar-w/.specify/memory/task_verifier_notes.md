# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The repository lacks the required `data/fixtures/monthly_sample.csv` and `contracts/dataset.schema.yaml` files, so the test cannot use a real pre‑fetched fixture or validate against the proper schema. Moreover, the provided `test_pipeline.py` creates a synthetic fixture instead of loading the real one and does not contain a clearly defined `test_pipeline_monthly_sync` function that checks `data/processed/synced.csv` against the missing schema. These essential artifacts and behavior are absent.
