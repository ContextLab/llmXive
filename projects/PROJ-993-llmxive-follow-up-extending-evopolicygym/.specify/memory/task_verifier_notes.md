# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013d** — declared artifact(s) missing/empty/invalid: data/discovered_envs.log, data/discovered_envs.json
- **T015b** — No schema definition file (e.g., CSV header list, JSON schema, or code comment) was provided; the evidence contains only the task description without any concrete artifact specifying the required columns and types. The implementer must supply a tangible schema definition for `sensitivity_report.csv`.
- **T013e** — declared artifact(s) missing/empty/invalid: data/discovered_envs.json
- **T013f** — declared artifact(s) missing/empty/invalid: data/discovered_envs.json, data/sensitivity_report.csv
- **T015c** — declared artifact(s) missing/empty/invalid: data/sensitivity_report.csv
- **T015a** — The provided `code/main.py` does not contain any logic that invokes `generate_all_dynamic_shift_envs` to apply `DynamicShiftEnvironment` to the discovered environments, nor does it implement a dedicated wrapper that checks for `data/sensitivity_report.csv` before doing so. Additionally, the required `data/sensitivity_report.csv` file is absent from the repository. Both the script behavior and the necessary data artifact are missing.
- **T023** — The provided `generator.py` includes a `handle_fallback` that logs to `data/fallbacks.log` and returns a `TemplateExplanation` object, satisfying the logging and object‑return parts. However, the implementation never returns a scalar reward signal as an alternative fallback, nor is there any code showing such a path. Consequently the requirement “return a `TemplateExplanation` object **OR a scalar_reward signal**” is not met. The missing scalar‑reward fallback must be added for the task to be complete.
