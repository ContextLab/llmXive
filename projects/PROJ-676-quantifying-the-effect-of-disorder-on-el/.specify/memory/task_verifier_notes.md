# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — The integration test file `tests/integration/test_pr_scaling.py` is present, but the required output `data/processed/scaling_fits.json` does not exist, so the test cannot pass and the schema validation cannot be performed. The missing JSON file must be generated (or added) for the task to be satisfied.
- **T013b** — declared artifact(s) missing/empty/invalid: data/processed/pr_raw_multiL.json
- **T013a** — declared artifact(s) missing/empty/invalid: data/processed/pr_raw_multiL.json, data/metadata/warnings.json, data/processed/pr_scaling_raw.json
- **T013c** — declared artifact(s) missing/empty/invalid: data/processed/w0_results.json
- **T015a#1** — declared artifact(s) missing/empty/invalid: data/processed/global_regression.json, data/processed/slope_test_results.json
- **T015b** — declared artifact(s) missing/empty/invalid: data/processed/slope_test_results.json, data/processed/bonferroni_results.json
- **T033a** — declared artifact(s) missing/empty/invalid: data/processed/w0_results.json, data/processed/scaling_fits.json
- **T023** — The repository contains a `code/compare_methods.py` file, but the required input files `data/processed/scaling_fits.json` and `data/processed/lyapunov_exponents.json` are absent, and the expected output `data/processed/method_agreement_report.json` was not generated. Consequently the script cannot be executed nor produce the required report, so the task is not genuinely completed.
- **T037** — The required `docs/physical_interpretation.md` file does not exist, and the provided `code/visualize.py` contains no implementation that computes a clean‑limit eigenstate, extracts the max‑amplitude site, calculates a spread, or writes a “Clean Limit: W=0” markdown table. Both the output document and the specific analysis code are missing.
