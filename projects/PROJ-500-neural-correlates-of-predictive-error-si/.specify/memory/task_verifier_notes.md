# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — No code, configuration, or log files were provided that demonstrate the system detecting missing metadata, issuing a warning, and skipping the affected dataset instead of crashing. Without such an artifact, the requirement of FR‑011 cannot be verified as satisfied.
- **T005c** — No evidence of a Git repository being initialized in the `src/` directory is provided (e.g., no `.git` folder, no `git init` command output, or related commit history). Without such artifact, the requirement that `git init` be run before any other Git operations is not satisfied.
- **T005d** — The required `state/projects/PROJ-500-neural-correlates-of-predictive-error-si.yaml` file does not exist, so no content hashes for `requirements.txt` and `pyproject.toml` are provided. The task’s core artifact is missing.
- **T005a** — No evidence of the required directories (`src/`, `tests/`, `contracts/`, `data/`, `analysis/`) is present; the implementer provided no file‑system listing or screenshots showing that the project structure exists. The task remains undone until the specified folder hierarchy is created and verified.
- **T009a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009b** — declared artifact(s) missing/empty/invalid: schema.yaml
