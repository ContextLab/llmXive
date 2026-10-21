# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/data/download.py exit=1; code/data/preprocess.py exit=1
- **T002** — The script and `data/processed/filtered.csv` exist with real RDKit-derived node/edge features and z-scored MW, but the required log artifacts (`logs/preprocess_summary.log` and `logs/failed_parsing.log`) are absent from the evidence, so there is no record of total/filtered/excluded row counts. Moreover, the code's `SCHEMA_PATH` points to `specs/001-.../contracts/dataset.schema.yaml` rather than the actual `contracts/dataset.schema.yaml`, and its fallback only catches `yaml.YAMLError` (not `FileNotFoundError`), suggesting validation ran against the minimal fallback schema — indeed, rows like `C
- **T003** — Requested task execution failed; rerun successfully: code/data/split.py exit=1
