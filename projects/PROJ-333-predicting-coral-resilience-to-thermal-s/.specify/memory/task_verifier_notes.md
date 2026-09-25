# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`code/`, `tests/`, `data/raw`, `data/processed`, `results/plots`, `specs/001-coral-resilience-prediction/`) being created is present; the implementer only provided a feature specification without any filesystem artifacts. The task’s core requirement—establishing the project directory structure—is therefore unmet.
- **T001b** — No `.gitignore` file was provided in the evidence, nor any listing of its contents showing the required exclusion patterns (`data/raw/*.fastq.gz`, `data/processed/*.rds`, `__pycache__`, `*.pyc`). The task cannot be considered fulfilled without the actual file.
- **T003a** — No `.flake8` configuration file is present in the provided evidence, and thus there is no content to verify that it contains `max-line-length = 88` and `ignore = E203,W503`. The required artifact is missing.
- **T003b** — declared artifact(s) missing/empty/invalid: pypyproject.toml
- **T004b** — No `specs/001-coral-resilience-prediction/amendments.md` file (or its contents) was presented, so we cannot verify that the change from BioProject PRJNA292777 to PRJNA321023 was documented as required. The required amendment record is missing.
