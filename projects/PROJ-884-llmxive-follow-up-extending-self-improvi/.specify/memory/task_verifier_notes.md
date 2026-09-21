# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001c** — No evidence of a `tests/` directory or its `unit` and `integration` subdirectories is provided, nor any verification that they exist and are writable. The required hierarchy is missing.
- **T024c** — The repository contains a non‑empty `code/bes/result_aggregator.py`, but the shown code stops at helper functions and provides no logic that actually reads the N‑specific logs and writes a combined `data/processed/bes_results.json`. Moreover, the required output file `data/processed/bes_results.json` is absent. The task’s core requirement – aggregating all logs into that single result file – is therefore not satisfied.
- **T016a** — The required `contracts/dataset.schema.yaml` file is missing, so the script cannot actually validate against the schema. Moreover, the provided script is truncated and shows no logic for loading the generated data from T014c-exec, indicating the implementation does not fulfill the task’s constraints.
