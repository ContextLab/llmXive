# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided showing that the required directories (`code/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`) actually exist in the repository; without such artifacts the claim cannot be verified.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or Black config) are present in the provided evidence, nor any scripts/CI steps showing ruff or black being set up. Without these artifacts, the requirement to configure linting (ruff) and formatting (black) is not satisfied.
- **T038** — declared artifact(s) missing/empty/invalid: data/processed/manifest.json
- **T040** — No test execution artifacts (e.g., pytest output logs, a passed/failed summary, or a CI report) are present. Without evidence that `pytest` was run and all unit/integration tests passed, the requirement cannot be confirmed. The implementer must provide the pytest run results showing a successful pass.
