# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The `contracts/requirements.schema.yaml` file is missing, causing the `validate_requirements_schema` test to fail (FileNotFoundError). Without the schema, the script cannot perform the required validation step, so the task’s core requirement is not met. Add the missing schema file (matching the expected JSON‑schema for a list of strings) and ensure the test passes.
- **T001** — Requested task execution failed; rerun successfully: code/data/fetch_heas.py exit=1
