# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T050** — No updated `loader.py` file is present, nor any log output or test run showing the exact counts and reasons for dropped instances. The required artifact (code change with explicit logging) and verification evidence are missing.
- **T051** — declared artifact(s) missing/empty/invalid: data/audit_logs/fallbacks.jsonl
- **T052** — No updated `glm_analyzer.py` file is present, nor any test script that mocks a missing `statsmodels` version and checks for a `RuntimeError`. The required version‑check implementation and verification evidence are missing.
- **T053** — No code changes adding a `--dry-run` flag to `run_baseline.py`, `run_high_fidelity.py`, or `run_7b_experiments.py` are present, nor are there any execution logs or output files showing the scripts run with `--dry-run` completing in under a minute and writing a subset of processed instances. The required artifacts (modified scripts and verification output) are missing.
- **T046** — The `threshold_validator.py` file is truncated (e.g., `def main()` lacks a body and no `if __name__ == "__main__"` guard), so it cannot be executed, and the required dataset `data/filtered_swe_bench_v1.parquet` is absent, preventing any row‑count check. Both the script implementation and the data file need to be completed for the task to be satisfied.
