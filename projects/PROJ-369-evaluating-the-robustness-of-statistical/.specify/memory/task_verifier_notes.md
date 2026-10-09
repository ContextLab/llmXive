# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001_new** — The required `state/` directory and its `structure_manifest.json` file are missing, so the manifest listing all created paths with SHA‑256 hashes was not generated. The other directories exist, but without the manifest the task is not fully satisfied.
- **T002** — The provided `requirements.txt` does not pin exact versions (it uses `>=`), omits the required `psutil` package, and includes many unrelated packages. No evidence of running `pip install -r requirements.txt` or generating a `requirements.lock` file is present. These issues must be fixed for the task to be considered complete.
- **T005** — The provided `src/utils/config.py` defines `_SEED` and `ALPHA_LEVEL` instead of the required `SEED` and `ALPHA`, and it does not contain the constants `NUM_NULL_PER_SERIES` or `MAX_LAG` at all. The task demands those exact global names and values, which are absent.
- **T019c** — declared artifact(s) missing/empty/invalid: data/processed/null_distributions/real/, data/processed/null_distributions/synthetic/, data/results/null_distribution_gate.json
- **T010_shuffled** — declared artifact(s) missing/empty/invalid: data/processed/metrics.json, data/processed/null_distributions/
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/metrics.json
- **T035** — declared artifact(s) missing/empty/invalid: tests/integration/test_pipeline.py
- **T037_profile** — declared artifact(s) missing/empty/invalid: data/results/profile_report.json
- **T037a_runner** — declared artifact(s) missing/empty/invalid: data/results/baseline_status.json
- **T039** — declared artifact(s) missing/empty/invalid: src/viz/plots.py
- **T039b** — declared artifact(s) missing/empty/invalid: src/viz/plots.py
- **T040** — declared artifact(s) missing/empty/invalid: data/results/performance_validation.json
- **T041** — declared artifact(s) missing/empty/invalid: data/results/final_summary.json
- **T057** — Requested task execution failed; rerun successfully: code/src/synthesis/verification.py exit=1
