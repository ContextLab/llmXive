# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T103** — The `validate.py` script does not import `List`/`Tuple` used in type hints, so it will raise a `NameError` before any validation runs, and the required `data/processed/descriptors.parquet` file is missing, preventing the script from being exercised as specified. Both issues must be fixed for the task to be satisfied.
- **T102** — The required files `tests/contract/validators.py`, `test_dataset_schema.py` and `test_model_output.py` exist, but `pytest tests/contract/ -q` fails because `validators.py` uses a deprecated `@root_validator` without `skip_on_failure=True`, causing a `PydanticUserError` during import. The contract tests therefore do not pass. Fix the validator definitions (e.g., replace `@root_validator` with `@model_validator` or add the needed flag) so that the tests run successfully.
- **T101** — Requested task execution failed; rerun successfully: code/data/generate_descriptors.py exit=1
