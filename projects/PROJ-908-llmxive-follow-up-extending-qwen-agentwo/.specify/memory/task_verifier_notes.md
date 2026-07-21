# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No files or directory listing for `projects/PROJ-908-llmxive-follow-up-extending-qwen-agentwo/` were provided, so the required project structure per `plan.md` cannot be verified as existing or correctly populated. The implementer must supply the actual folder contents showing the expected hierarchy and files.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black` settings) or scripts were presented, so there is no evidence that ruff and black have been configured for the project. The required artifacts are missing.
- **T006** — No evidence of the required `data/raw/` and `data/processed/` directories or a `.gitignore` file was provided; the claim lacks any artifact confirming the directory structure or ignore rules.
- **T007** — No evidence of any files under `specs/001-llmxive-followup/contracts/` was provided; the required schema definition files for “oracle”, “rules”, and “divergence” are missing, so the task is not satisfied.
- **T008** — No pytest configuration (e.g., `pytest.ini` or `conftest.py`) setting a fixed seed of 42 is present, nor are any integration test files or scaffolding shown. The required artifacts are missing, so the task is not satisfied.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/oracle_graph.json
- **T016** — No code, configuration files, or log output were presented showing that logging statements were added to the Oracle generation and validation steps. The required artifact—a modified codebase (or diff) with concrete logging implementation—is missing, so the task is not satisfied.
- **T020** — declared artifact(s) missing/empty/invalid: data/raw/cot_traces.json, code/inference/runner.py
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/extracted_rules.json
- **T024** — No code, data, or report was provided that implements the logic to flag “Extraction Uncertainty” nor adds an `excluded_metrics` field with counts for `extraction_uncertainty` and `cold_start`. The evidence consists only of the task description and spec excerpt, which does not satisfy the required deliverable.
