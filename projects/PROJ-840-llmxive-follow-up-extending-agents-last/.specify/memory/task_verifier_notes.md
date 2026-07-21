# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The required output file `data/raw/golden_subset.json` does not exist, and the provided `generator.py` snippet is incomplete (truncated) so we cannot verify that it actually calls `verify_pairing` or produces data matching the specified schema. The task’s core deliverable is missing.
- **T015b** — The repository contains `code/data/golden_set_generator.py`, but the script is incomplete (truncated) and the required output file `data/raw/human_annotated_subset.json` does not exist. Without a generated JSON containing ≥10 labeled traces, the task’s core requirement is unmet.
- **T012** — The `goal_validator.py` uses the wrong ID regex (`\b(\w+\d+)\b` instead of the required `\b(\w+_\d+)\b`) and the expected output file `data/processed/static_constraints.json` is not present. Both the pattern specification and the required artifact are missing/incorrect.
- **T013** — The repository contains `code/classification/state_validator.py`, which implements loading, comparison, and accuracy calculation, but the required input file `data/raw/human_annotated_subset.json` is absent, so the validator cannot be run against the golden data. Without this file (or a generated reconstruction), the task’s core requirement is unmet.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/classification_report.json
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/baseline_results.json, data/processed/intervention_results.json
- **T028a** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_N1.json
- **T028b** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_N3.json
- **T028c** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_N5.json
- **T028d** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_analysis.json
