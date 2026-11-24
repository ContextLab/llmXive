# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `data/checksums.txt` file is missing and the BIDS‑structured directory tree is not present under `data/raw/` (only a zip and a .gitkeep). Moreover, `code/download.py` uses the Python `requests` library instead of `wget`/`curl`, violating the specified implementation detail. The task’s download and verification requirements are therefore not met.
- **T002** — The required output file `data/processed/subsampled_raw.fif` is missing, and the unit‑test log shows failures (NameError for `np`) indicating the preprocessing functions are not verified to work. The pipeline therefore does not produce the specified subsampled, filtered, re‑referenced data.
- **T004** — Requested task execution failed; rerun successfully: code/preprocess.py exit=1
