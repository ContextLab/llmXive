# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree, files, or any filesystem artifacts were provided; there is no evidence that `data/raw`, `data/corrupted`, `code`, `results`, and `tests` directories exist, nor that empty `__init__.py` files were created in `code/` and `tests/`. The required project structure is missing.
- **T002** — No evidence of a Python project initialization was provided—there is no directory structure, no `pyproject.toml`, `requirements.txt`, `environment.yml`, or any other file listing the required dependencies (pandas, numpy, scipy, statsmodels, matplotlib, seaborn, pyyaml, pytest). Without such artifacts, the claim that the project has been set up with those packages cannot be verified.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or setup scripts were presented. Without such artifacts, the requirement to configure ruff/flake8 and Black is not satisfied.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005b** — The test file `tests/unit/test_schema_validation.py` exists and correctly checks that `error_rates` is a non‑empty list of numeric values, but it also asserts that `contracts/injection.schema.yaml` exists – that file is missing from the repository, so the test cannot actually load the schema and will fail. The required schema file must be present (or the test adjusted) for the task to be fulfilled.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T014** — The repository lacks the required `contracts/result.schema.yaml` and `state/simulation_artifacts.yaml` files, and the provided `code/simulate.py` is truncated before any logic that validates synthetic/null‑hypothesis outputs, records SHA‑256 checksums, or writes status to the state file. Consequently the task’s core requirements are not met.
- **T047** — declared artifact(s) missing/empty/invalid: state/citation_log.yaml
- **T019c** — The repository lacks the required `contracts/dataset.schema.yaml` file, so validation cannot be performed. Moreover, the provided `code/download.py` (truncated) does not show any implementation of schema validation, type coercion, or empty‑string‑to‑NaN replacement before writing cleaned files to `data/raw/cleaned/`. Both the schema and the cleaning logic are missing, so the task is not satisfied.
- **T019d** — declared artifact(s) missing/empty/invalid: state/dataset_checksums.yaml
