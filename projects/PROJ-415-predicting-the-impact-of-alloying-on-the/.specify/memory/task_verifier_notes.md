# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The submission contains no linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.flake8`, or related scripts) and provides no evidence that ruff, flake8, or black have been installed or configured. Consequently the task of configuring these tools is not satisfied.
- **T009** — The `tests/contract/test_schema.py` file is present and contains validation logic, but the required schema file `contracts/diffusion_record.schema.yaml` is missing, causing the test to fail or be skipped. The task is not fully satisfied until the referenced schema file exists and is non‑empty.
- **T024** — declared artifact(s) missing/empty/invalid: models/linear_coef.json
