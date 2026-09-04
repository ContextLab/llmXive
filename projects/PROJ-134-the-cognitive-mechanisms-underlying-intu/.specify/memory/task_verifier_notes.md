# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The repository contains `code/data/simulation_mfq.py` which loads the MDES report and validates the ground‑truth effect, but the required output file `data/processed/synthetic_mfq.csv` is absent. Consequently the deliverable (a non‑empty CSV with the specified columns) has not been produced, so the task is not satisfied.
- **T014** — The repository contains `code/data/simulation_stories.py`, but the required output file `data/processed/synthetic_logs.csv` does not exist, so the deliverable cannot be verified for the required columns. The task therefore remains unfinished.
- **T018** — The repository contains a partially shown `code/utils/hashing.py`, but the file is truncated and does not demonstrate any logic that scans simulation‑derived CSVs or writes their checksums to `state/artifact_hashes.yaml`. Moreover, the required `state/artifact_hashes.yaml` file is absent. Both the integration and the state update are therefore missing.
- **T038** — declared artifact(s) missing/empty/invalid: code/unity_verification.py
