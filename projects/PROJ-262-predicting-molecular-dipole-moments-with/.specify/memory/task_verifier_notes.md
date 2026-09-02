# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019a** — The provided `handle_missing_coords.py` is incomplete (truncated) and never reaches the part that writes `data/reports/excluded_molecules.csv`. Moreover, the expected CSV file is absent from the repository. The task’s required output file is therefore missing.
- **T016a** — The script `create_subset.py` correctly implements deterministic subset creation with seed 42 and size 5000, but the required output file `data/processed/subset_final.parquet` is missing, so the task’s primary artifact is not present. The implementer must run the script (or otherwise generate) to produce the parquet file at the specified location.
