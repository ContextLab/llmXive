# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The provided `scripts/recovery_reset.py` exists but the shown code does not include a main entry that checks `research.md` and exits with the required status codes, nor does it demonstrate scanning the `tests/` directory or actually modifying `tasks.md` to reset tasks T015‑T035. Without these parts, the script does not fulfill the full specification. The next implementer should add the missing execution logic, ensure the script scans `tests/`, updates `tasks.md` as described, and returns the correct exit codes.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — declared artifact(s) missing/empty/invalid: src/data/generators/structural_validation_generator.py, data/raw/structural_validation_data.csv, schema.yaml
- **T010a** — The orchestrator script `src/cli/run_pipeline.py` is truncated and does not contain the required argument parsing, citation‑validation gate, or full execution flow, and it ends with a syntax error. Moreover, the required modules `src/data/generators/structural_validation_generator.py` and `src/data/processing/feature_engineering.py` are missing entirely, so the script cannot invoke the necessary generators or feature‑engineering steps. The task’s core requirements are therefore not satisfied.
- **T010b** — The required `.github/workflows/ci.yml` file is missing, so the CI workflow has not been created or configured as specified. Without this file, the verification step cannot be performed.
