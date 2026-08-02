# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017b** — The script `code/01_download_and_filter.py` is truncated and never reaches the filtering or file‑writing logic; the required output files `data/processed/eligible_subjects.csv` and `data/processed/excluded_subjects.log` are absent. The status artifact shows an error and zero eligible subjects, and there is no evidence that the script exits with `sys.exit(2)` when no eligible subjects are found. The task’s core functionality is therefore not fulfilled.
