# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — I inspected `code/download.py` (present) and the required output artifacts. The three CSV files (`data/raw/band_gap.csv`, `formation_energy.csv`, `thermal_conductivity.csv`) and their corresponding metadata JSON files are absent, and the checksum manifest is missing. Running the provided `code/tests/test_download.py` fails with a 401 error during download and errors due to missing files, confirming that the implementation does not produce the required datasets, metadata, or manifest. The task therefore lacks the essential artifacts and does not meet the specification.
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=2
