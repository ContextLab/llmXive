# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T063** — The provided `src/environment/runner.py` does not contain any logic that checks for the presence or non‑emptiness of `data/processed/full_sweep_results.json`, nor does it exit with code 1 and the required error message. Additionally, the expected data file is missing from the repository. Consequently, the task’s verification requirement is not satisfied.
- **T065** — The required output file `data/processed/heavy_tailed_results.json` does not exist, and the supporting `full_sweep_results.json` is also missing, so the heavy‑tailed validation was not run nor verified as independent. The task’s deliverable is therefore not satisfied.
- **T067** — The required `scripts/run_full_suite.sh` script is absent, and the expected output file `data/processed/statistical_report.json` does not exist, so the end‑to‑end test cannot be run nor verified. The task’s deliverables are missing.
