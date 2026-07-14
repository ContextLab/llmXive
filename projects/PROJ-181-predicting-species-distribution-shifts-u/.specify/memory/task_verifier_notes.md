# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or file listing was provided to confirm that `projects/PROJ-181-predicting-species-distribution-shifts-u/` and all required subdirectories exist; without such evidence the claim cannot be verified.
- **T002** — No `requirements.txt` file (or any other artifact) was provided showing a Python 3.11 project with the exact pinned dependency versions listed in the task. The implementer’s claim lacks the required concrete file, so the task is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., .flake8, pyproject.toml with black settings, or a pre‑commit hook) are present in the provided evidence, so the requirement to configure flake8 and black is not satisfied.
- **T005** — No code, configuration file, or initialization script that sets up a logger to write to the `logs/` directory is present in the provided evidence. The required logging infrastructure artifact is missing, so the task is not satisfied.
- **T009** — The provided information contains no evidence that a `contracts/` directory exists, nor that the required `model_metrics.schema.yaml` and `occurrence.schema.yaml` JSON Schema files are present or contain any content. Without these artifacts, the task requirement is not satisfied.
