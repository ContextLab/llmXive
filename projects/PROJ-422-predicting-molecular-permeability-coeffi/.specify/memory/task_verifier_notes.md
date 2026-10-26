# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The `code/data/split.py` script exists, reads the processed Parquet file, drops rows with null targets, handles ≤5‑row leave‑one‑out splits, and writes both CSV and Parquet files. However, it does **not** enforce the required ≤5 percentage‑point class distribution difference for polymer‑type stratification, nor does it provide the `stratified_split` / `execute_split` APIs that the unit tests expect (as shown by multiple failures in `tests/unit/test_split.py`). Consequently the stratification constraint verification and the unit‑test suite are not satisfied.
- **T004** — Requested task execution failed; rerun successfully: run_all.sh exit=1
