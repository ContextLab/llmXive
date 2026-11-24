# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — Requested task execution failed; rerun successfully: code/services/executor_full.py exit=1
- **T006** — The provided `code/utils/step_expander.py` correctly reads both log files and writes `data/processed/step_outcomes.json` with the required fields and the `exclude_from_regression` flag, and the JSON file contains 10 records. However, there is no evidence of a dedicated `StepOutcome` model (e.g., a Pydantic or dataclass definition) as required by FR‑005, and the repository contains no such model file. Adding the missing model definition will satisfy the full task specification.
- **T007** — Requested task execution failed; rerun successfully: code/services/analyzer.py exit=1
- **T008** — Requested task execution failed; rerun successfully: code/services/analyzer.py exit=1
