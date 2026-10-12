# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The filtered dataset `data/processed/filtered_esol.csv` contains an extra column `molecule_id` (see the failing test `test_filtered_dataset`), so it does **not** have exactly the required columns `smiles` and `logP`. This violates the schema‑validation requirement of Task T001. The other artifacts (checksums, power analysis report, scaffold counts, splits, exclusion log) exist and appear correct, but the core output dataset is malformed. The implementer must remove the `molecule_id` column before writing the filtered CSV (or otherwise ensure the output matches the schema).
- **T002** — Requested task execution failed; rerun successfully: code/02_tda_computation.py exit=1
