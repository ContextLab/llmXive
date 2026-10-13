# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The quickstart.md and directory layout exist, and the setup script logs successful GEO access, but the `data/raw/` directory is empty and no evidence is provided that SHA‑256 checksums for raw files were generated and stored in `data/project_state.yaml`. The task’s core “data hygiene” requirement (checksum generation and recording) is therefore unmet. Adding the raw input files, computing their checksums, and persisting them in the project state YAML will be needed.
- **T002** — Requested task execution failed; rerun successfully: code/data_pipeline.py exit=1
