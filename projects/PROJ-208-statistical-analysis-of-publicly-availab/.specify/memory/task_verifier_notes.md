# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009a** — The repository contains `code/data/loader_hf.py`, but the script never writes the fetched data to `data/raw/github_issues_raw_hf.parquet` nor does it perform full schema validation against `contracts/dataset.schema.yaml`. Moreover, the required output parquet file and the schema file are absent from the project. Consequently the task’s deliverables are not present.
- **T009b** — The required output file `data/raw/github_issues_raw_api.parquet` does not exist, and the provided `loader_api.py` is truncated (no visible logic for fetching issues, handling stop conditions, or writing the Parquet file). Without the generated dataset, the task’s deliverable is not satisfied.
