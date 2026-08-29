# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007a** — The repository contains `code/01_download_data.py`, but the script includes placeholder checksum values and incomplete download logic (truncated and only mentions a representative subset). Moreover, the required output file `data/interim/data_source_manifest.json` is absent. Consequently, the task’s core requirements—fetching the full dataset, verifying checksums, and generating the manifest—are not satisfied.
- **T035a** — The required `data/processed/features.csv` does not exist, so the schema validation tests cannot run, and the contract file `contracts/feature_schema.schema.yaml` is also missing. Both required artifacts are absent, so the task’s validation requirement is not satisfied.
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/correlations_corrected.csv
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
