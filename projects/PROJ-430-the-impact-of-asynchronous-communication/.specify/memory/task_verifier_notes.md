# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The required output file `data/raw/events.json` does not exist, and the provided `code/data_ingestion.py` is only partially shown (truncated) with no visible logic that writes the JSON file, handles the `--fetch` CLI flag, uses the specified sample repo IDs, or computes the inter‑arrival time variance. Consequently the task’s core deliverables are missing.
- **T010b** — declared artifact(s) missing/empty/invalid: tests/unit/test_ground_truth.py
- **T015** — declared artifact(s) missing/empty/invalid: data/derived/project_metrics.csv
- **T016** — declared artifact(s) missing/empty/invalid: data/logs/rate_limit_events.log
- **T021b** — The repository lacks the required input data files (`data/derived/pair_sentiment.parquet` and `data/derived/project_metrics.csv`) and the expected output file (`data/derived/project_cohesion_scores.csv`). Moreover, the provided `code/sentiment.py` excerpt does not show any implementation of the project‑level weighted‑average aggregation described in the task. Without these artifacts, the task’s requirements are not met.
