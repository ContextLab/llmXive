# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `tests/`, `data/`) is provided; the response contains only specification text and no actual project structure on disk. The task’s core deliverable is missing.
- **T003** — No linting or formatting configuration files (e.g., .flake8, pyproject.toml/black settings, pre‑commit hooks) or documentation were provided; the only evidence is a feature specification unrelated to linting. The required artifacts to show that flake8 and black are configured are missing.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No evidence of the `data/raw/` and `data/processed/` directories being created is provided; the artifact list is empty, so the required folder structure is missing.
- **T012** — The provided `tests/contract/test_dataset.py` is incomplete (truncated) and references a schema file that does not exist on disk (`dataset.schema.yaml` is missing), so the contract tests cannot be executed as required. The task therefore is not fully satisfied.
