# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/verify_data_source.py exit=1
- **T002** — The required raw files `data/raw/nist.csv`, `data/raw/zenodo.csv`, and `data/raw/materials_project.csv` are missing, and `data/raw/checksums.txt` only lists a checksum for `example.csv` rather than the three expected source CSVs. Consequently the task’s core requirement is not satisfied.
- **T003** — The execution log shows the script ran successfully and created `data/raw/adhesion_raw_units.json`, but the task requires a file named `data/raw/adhesion_units.json`. That exact JSON file is missing, so the required artifact is not present. The implementer must generate the correctly‑named `adhesion_units.json` (or rename the existing file) to satisfy the task.
- **T004** — Requested task execution failed; rerun successfully: code/preprocess.py exit=1
