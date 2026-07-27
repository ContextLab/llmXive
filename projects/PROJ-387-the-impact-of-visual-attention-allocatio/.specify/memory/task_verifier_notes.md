# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016** — No code, script, or log file was provided that demonstrates the ingestion process halting with exit code 1 and emitting the required `DATA_BLOCKER: Missing required variables` message when required columns are absent. The claim lacks any tangible artifact to verify the required behavior.
- **T017** — No code, script, or log output was provided that implements the required logging behavior (checking dataset count, logging the `DATA_BLOCKER` message and exiting on zero, or logging `Ingestion Success Rate: X%` on non‑zero). Without such artifacts, the task’s deliverable cannot be confirmed as completed.
- **T020** — declared artifact(s) missing/empty/invalid: results/lmm_summary.csv
- **T021** — No code, script, or data artifact was provided that implements a loop over attention‑metric and valence‑category combinations and stores the resulting model outputs. The required implementation and stored results are missing.
- **T022** — declared artifact(s) missing/empty/invalid: results/correction_results.json
- **T023** — The repository contains a partially‑implemented `sensitivity.py` but the script’s entry point is truncated and never invokes `run_sensitivity_analysis` with the required thresholds {0.01, 0.05, 0.1}. Moreover, the expected output file `output/results/sensitivity_analysis.json` is absent from the disk. The deliverable is therefore not present and the implementation does not demonstrably meet the task’s specifications.
- **T024** — No artifact showing result objects with an `association_label: "associational"` field was provided; without such output the requirement of appending the label to all results is not demonstrated.
- **T025** — The submission contains only the task description and project specifications; there is no code, script, or log output that implements error handling for missing recall scores, logs a warning, skips the problematic rows, and continues processing. Consequently, the required artifact (the implemented error‑handling logic) is missing.
- **T043** — declared artifact(s) missing/empty/invalid: results/final_report.md
