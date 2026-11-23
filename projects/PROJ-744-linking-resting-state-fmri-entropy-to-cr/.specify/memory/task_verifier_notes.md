# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007b** — declared artifact(s) missing/empty/invalid: data/processed/valid_subjects.csv
- **T008** — declared artifact(s) missing/empty/invalid: conftest.py
- **T017** — The repository contains a partially shown `code/entropy.py`, but the file is truncated and does not demonstrate the required orchestration, subject looping, or memory‑chunking logic. Moreover, the required output `data/processed/entropy_metrics.csv` is absent. The task’s core deliverables are therefore not present.
- **T017b** — The `code/entropy.py` file defines helper functions for RAM tracking but the provided excerpt (and the truncated remainder) shows no invocation of `_reset_peak_ram`, `_update_peak_ram`, or `_log_peak_ram` during the actual entropy computation, nor is the required `data/logs/ram_usage.log` file present. Consequently the task’s requirement to log peak RAM usage for the full run is not satisfied.
- **T043** — declared artifact(s) missing/empty/invalid: data/processed/surrogate_results.csv
- **T044** — The required `data/processed/surrogate_validation_report.csv` does not exist, and the provided `code/sensitivity.py` is truncated and lacks any implementation that compares real vs. surrogate entropy, computes differences, determines pass/fail, or writes the specified CSV. The validation logic and output artifact are therefore missing.
