# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`code/`, `tests/`, `data/raw`, `data/processed`, `results/plots`, `specs/001-coral-resilience-prediction/`) is provided; the claim cannot be verified. The implementer must create and show the populated project folder structure.
- **T001b** — No `.gitignore` file was presented in the evidence, and no content showing the required exclusion patterns (`data/raw/*.fastq.gz`, `data/processed/*.rds`, `__pycache__`, `*.pyc`) was provided. The required artifact is therefore missing.
- **T003a** — No `.flake8` file was presented in the evidence; the required configuration with `max-line-length=88` and `ignore=E203,W503` is absent, so the task is not satisfied.
- **T011** — I looked for a `tests/integration/` directory containing test scaffolding and mock FASTQ files, but no such files or code were provided. Without the integration test files, the requirement to verify pipeline flow with mock data is not satisfied. The next implementer must add the integration test suite and include small mock FASTQ files in the specified location.
