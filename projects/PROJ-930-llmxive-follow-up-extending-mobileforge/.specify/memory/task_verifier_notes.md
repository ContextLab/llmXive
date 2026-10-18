# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — `code/requirements.txt` exists and the install log at `outputs/install_log.txt` shows a successful `pip install -r code/requirements.txt`, but the file contains 12 lines: the 11 required pins plus an extra `pyarrow==14.0.1`, violating the "exactly the 11 required lines (no extra packages)" requirement. Remove the pyarrow line (the root-level `requirements.txt` shows the correct 11-line content).
- **T009** — Requested task execution failed; rerun successfully: code/data/raw/validate_extraction_dataset.py exit=1
