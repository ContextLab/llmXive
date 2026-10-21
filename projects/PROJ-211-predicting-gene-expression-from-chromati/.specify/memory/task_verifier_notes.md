# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The repository contains `code/download_encode.py` and a `data/raw/checksums.csv`, but the required output files `data/raw/encode_counts_{cell_line}.csv` and `data/raw/encode_peaks_{cell_line}.bed` for the five cell lines are absent. The script falls back to generating synthetic files (`synthetic_counts.csv`, `synthetic_peaks.bed`) when ENCODE queries fail (CI_MODE=1), and the checksums CSV records only those synthetic files. Additionally, the integration test `tests/integration/test_download.py` is missing, so no verification of column headers or schema compliance is possible. The task’s core
- **T003** — Requested task execution failed; rerun successfully: code/preprocess.py exit=1
