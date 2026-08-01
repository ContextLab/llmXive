# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — declared artifact(s) missing/empty/invalid: data/raw/metabolite_matrix.csv
- **T003** — The required artifact `data/raw/checksums.json` is missing, so no checksum verification was performed and the abort condition cannot be evaluated. The task’s core output does not exist.
- **T004** — No `data_pairing.json` or `feature_filtering.csv` files were supplied; the response contains only the task description and spec excerpt, with no actual logging utilities, JSON entries, or CSV output. The required artifacts are missing, so the task is not satisfied.
- **T005** — No code, script, or log file is provided that implements a runtime check of the pairing rate on the downloaded data and aborts with error E‑PAIRING when the rate falls below 95 %. The required artifact (e.g., a function/module, unit test, or execution log demonstrating the abort behavior) is absent.
- **T006** — declared artifact(s) missing/empty/invalid: data/processed/paired_samples.csv
- **T007** — No code, configuration, or documentation for the required error handling framework (E-DATASET, E-PAIRING, E-TIMEOUT, E-POWER) was presented; the claim lacks any artifact demonstrating implementation per plan.md.
- **T008** — No `logs/power_analysis_report.json` file was presented, and no content showing N, power, effect_size, alpha, or test_type was provided. The required power‑analysis output is therefore missing.
