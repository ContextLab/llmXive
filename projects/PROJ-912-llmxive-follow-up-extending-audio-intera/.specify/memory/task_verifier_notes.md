# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided information contains only the feature specification and user stories; there is no evidence that the required directories (`code/`, `data/`, `tests/`, `state/`) actually exist or contain any files. The implementer has not supplied any artifact confirming the project structure was created.
- **T003** — No configuration files (e.g., `pyproject.toml` with Black settings, `ruff.toml` or `ruff.toml` entries, or CI scripts invoking ruff/black) are present in the `code/` directory, nor any evidence that linting/formatting has been set up. Without these artifacts, the requirement to configure ruff and black cannot be confirmed.
- **T008** — No GitHub Actions YAML file or any other environment‑configuration artifact was provided; the only content shown relates to audio model user stories, not to a CI runner setup. The required CI configuration is missing, so the task is not satisfied.
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/robustness_metrics.csv
