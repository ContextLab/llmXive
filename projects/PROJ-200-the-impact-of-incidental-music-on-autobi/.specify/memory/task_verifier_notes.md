# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T120** — The repository contains a `write_parquet` implementation, but the required output file `data/processed/ingested_cohort.parquet` is missing, indicating the function has not been executed (or does not write to the expected default location). The task’s core deliverable—a parquet file at the specified path—is absent.
- **T122** — The `update_state_yaml` function in `code/utils.py` is cut off mid‑implementation (ends with “st”) and does not contain the logic to write the updated data back to `state.yaml`. Additionally, the required `state.yaml` file is absent from the repository. Both the implementation and the target artifact are missing, so the task is not satisfied.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/ingested_cohort.parquet, state.yaml
- **T123** — The repository contains a `write_parquet` implementation, but the required output file `data/processed/user_track_pairs.parquet` is not present. Without the actual Parquet file being generated, the task’s primary deliverable is missing. The next implementer must ensure the function is invoked (or hard‑coded) to create that file and verify its existence.
