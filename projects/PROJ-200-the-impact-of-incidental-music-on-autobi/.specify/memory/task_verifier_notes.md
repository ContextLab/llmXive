# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The repository does not contain a `state.yaml` file (it is listed as MISSING), and the `state_manager` implementation creates a default state with top‑level keys `metadata` and `files`, not the required `artifact_hashes`, `updated_at`, and `config`. Consequently the task’s requirement to initialise `state.yaml` with those specific keys is not met.
- **T001** — The `quickstart.md` does contain the required `python -m code.main --demo` command, but `requirements.txt` does not pin all dependencies (only `python-levenshtein` is version‑pinned) and the required test file `tests/unit/test_quickstart.py` is missing, so the CI checks cannot be satisfied.
- **T002** — The two schema files (`contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`) are present and contain plausible JSON‑Schema definitions, but there is no evidence that `jsonschema` validation was actually run against the generated parquet/CSV files nor that all such files passed validation. Provide validation logs or test results confirming the schemas successfully validate the produced data.
- **T003** — Requested task execution failed; rerun successfully: code/simulate_demo.py exit=1
