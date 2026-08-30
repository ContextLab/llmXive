# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016** — The repository contains the `create_subset.py` script that correctly implements deterministic shuffling with seed 42 and writes to `data/processed/subset_final.parquet`, but the required output file `subset_final.parquet` is absent, indicating the subset was never generated or saved. The task’s core deliverable (the parquet file) is missing.
- **T019** — The required `data/reports/excluded_molecules.csv` file does not exist, nor does the `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` file. The provided `handle_missing_coords.py` script is incomplete (truncated) and never writes the CSV or updates the YAML with an artifact hash. The task’s deliverables are therefore missing.
