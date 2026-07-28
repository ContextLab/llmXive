# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`data/raw`, `data/results`, `code`, `tests/unit`, `tests/contract`, `contracts`, `projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/`) being present on disk is provided; without visible artifacts we cannot confirm the structure was created.
- **T003** — No `quickstart.md` file was presented; there is no evidence of its existence, content, or installation instructions, so the required artifact is missing.
- **T004** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The test file `tests/contract/test_schemas.py` is present, but the required schema `contracts/task.schema.yaml` does not exist, causing the test to fail (or be skipped) and preventing any real validation of `tasks.json`. The missing schema file must be added for the contract test to be functional.
- **T012** — The provided `tests/contract/test_schemas.py` ends abruptly inside `test_skills_json_schema` and does not contain the full validation logic or overlap‑metric checks. Moreover, the required schema file `contracts/skill.schema.yaml` is absent, so the test cannot even load the schema. Both the test implementation and the referenced schema are missing, so the task is not satisfied.
- **T015** — The repository lacks the required output files `data/raw/skills.json` and `data/raw/tasks.json`, and the shown portion of `code/generate_data.py` does not contain any JSON‑serialization logic that writes those files (the code is truncated before any file‑output code). The task’s core requirement—producing the two JSON files with embedded metadata—is therefore not satisfied.
