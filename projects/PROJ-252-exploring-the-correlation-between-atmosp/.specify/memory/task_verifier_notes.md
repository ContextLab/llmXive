# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — The provided `preprocess.py` only shows configuration loading and schema validation; there is no implementation of the left‑censored moving‑average calculation or the exclusion of the period immediately before the event window. Additionally, the required root‑level `config.yaml` is missing, so the verification step cannot compare values as specified. The task’s core logic is not present.
- **T017** — The required output `data/processed/master_dataset.csv` and its SHA‑256 checksum file are absent, and the referenced schema files (`contracts/earthquake.schema.yaml`, `contracts/pressure-anomaly.schema.yaml`) are missing, so the verification steps cannot be performed. The task therefore has not been fulfilled.
