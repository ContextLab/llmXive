# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No pytest configuration file (e.g., pytest.ini, pyproject.toml, or conftest.py) or the required `tests/contract/test_schemas.py` skeleton was found in the repository; without these artifacts the task’s deliverables are missing.
- **T009** — No evidence of a `tests/contract/test_dataset_schema.py` file was provided; without the actual test file (non‑empty and containing schema contract checks) the requirement is not satisfied. The implementer must add the contract test file that validates the dataset schema output from T006.
- **T010** — No `tests/unit/test_mutation.py` file or its contents were provided; without the actual unit test code we cannot confirm that a test for variable‑rename and comment‑removal mutation logic exists or is non‑empty. The required artifact is missing.
- **T011** — No evidence of a `tests/unit/test_synthetic_validity.py` file containing a unit test that parses synthetic issues with `ast` was provided; the required artifact is missing, so the task is not satisfied.
