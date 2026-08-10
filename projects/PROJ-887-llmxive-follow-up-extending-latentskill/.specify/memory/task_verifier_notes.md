# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T022e** — The required output file `data/processed/eval_tasks.yaml` does not exist, so the held‑out task list was never generated. Without this file the task’s core requirement is unmet. The implementer must run/finalize the script so that the YAML file is created and populated with the actual task IDs.
- **T030** — The `src/validation/linearity_check.py` file exists, but the required input `data/processed/pairs.yaml` is missing, causing the script to fail when run. Consequently no `data/results/linearity_check.json` is produced, so the task’s core output (correlation value and validity flag) is absent. The implementation must be completed with a valid `pairs.yaml` and ensure the script writes the JSON result.
