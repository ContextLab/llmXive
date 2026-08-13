# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T048** — The repository contains a partially implemented `loader.py` with checksum utilities, but the required `data/processed/subtle_cue_subset.parquet` file is absent, and no `integrity_log.txt` is created. Moreover, the code does not show an automatic verification call for that specific file before training/inference, nor does it log the result to the specified log file. These missing artifacts and integration steps must be added to satisfy the task.
- **T049** — The provided `runner.py` is truncated and does not contain the required batch‑size‑adjustment loop, RAM‑threshold checks, retry/skip logic, or code that writes the final batch size to `data/processed/inference_config.yaml`. Moreover, the `inference_config.yaml` file is missing entirely. The task’s core requirements are therefore not satisfied.
- **T050** — declared artifact(s) missing/empty/invalid: code/models/student.py, data/processed/model_fingerprints.csv
