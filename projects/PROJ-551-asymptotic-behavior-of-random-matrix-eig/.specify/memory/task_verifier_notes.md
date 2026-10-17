# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The three required schema files (`contracts/simulation_run.schema.yaml`, `contracts/eigenvalue_result.schema.yaml`, `contracts/aggregated_threshold.schema.yaml`) are reported as missing and no content for them is provided, so we cannot verify that proper JSON‑Schema definitions were created. Consequently the contract‑validation test, while present and passing, cannot be confirmed to validate against the intended schemas. The task therefore remains incomplete.
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=2
- **T005** — The required `data/processed/mc_results.csv` and `data/processed/convergence_data.json` files are present, but the schema‑validation test (T001) fails: the test cannot find `contracts/simulation_run.schema.yaml` and also reports the CSV as missing, indicating the verification step does not succeed. The missing schema file (and any path adjustments needed for the test) must be added for the task to be considered complete.
- **T006** — Requested task execution failed; rerun successfully: code/analysis/threshold_fit.py exit=1
- **T007** — Requested task execution failed; rerun successfully: code/analysis/aggregate_thresholds.py exit=1
