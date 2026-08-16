# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The repository lacks a `validate_sample_size` implementation in `code/download.py` (no such function is present in the shown code) and the required output file `data/processed/sample_size_report.json` does not exist. Both the core logic and the deliverable artifact are missing.
- **T014** — No evidence of a `logs/download.log` file was provided; the response contains only the task description and specifications, with no actual log file or its contents showing progress updates. The required artifact is missing.
- **T018c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/retrieval_results.csv
- **T021** — No code, configuration, or log files were provided that demonstrate the added error‑handling logic (logging failures, attempting upper‑limit derivation, and continuing execution). Without concrete artifacts, we cannot verify that the requirement has been implemented.
- **T025c** — declared artifact(s) missing/empty/invalid: data/processed/bootstrap_ci.json
- **T026** — declared artifact(s) missing/empty/invalid: results/robustness_report.json
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/regression_results.json
- **T028** — No code, script, or documentation was presented that shows a Tobit regression with L2 (Ridge) regularization being invoked when variance inflation factors exceed 5, nor any evidence that L1 or Elastic Net were avoided. The required fallback implementation is missing.
