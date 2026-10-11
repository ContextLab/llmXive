# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required `per_sample_errors.schema.yaml` contract is either missing or does not define the full column list (the unit test reports “incomplete column entry” for each required field), causing the skeleton verification test to fail. The directory structure is present, but the schema file must be created/filled with the specified columns.
- **T002** — The repository contains `code/download.py` which implements the required download, capping, checksum, and metadata logic, but the `data/raw/` directory is empty – no CSV dataset files, no `<dataset>_metadata.json` files, and no `sha256_manifest.txt`. Additionally, the unit‑test log shows failures (NameError in the tests), indicating the implementation has not been verified to work. The required output artifacts are missing, so the task is not fully satisfied.
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
