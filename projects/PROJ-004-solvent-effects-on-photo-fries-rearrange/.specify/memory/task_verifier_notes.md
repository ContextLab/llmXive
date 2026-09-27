# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T060** — The provided `instrument_calibration_log.py` defines defaults and functions but the evidence shows no code that writes the calibration log to `data/processed/instrument_calibration_log.json`, and that JSON file is missing from the repository. The task’s core output is therefore not present.
- **T061** — The required output file `data/processed/material_balance_report.csv` is not present, and the provided `material_balance.py` is truncated before any report‑generation logic, so there is no evidence that the script actually creates the CSV with the requested quantities and error margins. The missing CSV must be generated for the task to be considered complete.
