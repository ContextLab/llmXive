# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013d** — declared artifact(s) missing/empty/invalid: data/discovered_envs.log, data/discovered_envs.json
- **T015b** — No schema definition file (e.g., CSV header list, JSON schema, or code comment) was provided; the evidence contains only the task description without any concrete artifact specifying the required columns and types. The implementer must supply a tangible schema definition for `sensitivity_report.csv`.
- **T013e** — declared artifact(s) missing/empty/invalid: data/discovered_envs.json
- **T013f** — declared artifact(s) missing/empty/invalid: data/discovered_envs.json, data/sensitivity_report.csv
- **T014** — The required `data/shift_validation.log` file does not exist, so the logging of failures and skipping logic cannot be verified. Without this artifact, the task’s core requirement (logging and skipping environments based on the p‑value) is not satisfied.
- **T015c** — declared artifact(s) missing/empty/invalid: data/sensitivity_report.csv
- **T015a** — The provided `code/main.py` does not actually invoke `generate_all_dynamic_shift_envs` to apply `DynamicShiftEnvironment`, and the required `data/sensitivity_report.csv` file is absent, causing the script’s pre‑flight check to fail. The wrapper therefore does not meet the orchestration and verification requirements.
