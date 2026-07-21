# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory `projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/` or any of its contents were presented; the claim provides no tangible artifact to confirm the required project root structure exists. The task therefore remains unverified and incomplete.
- **T001b** — No evidence was provided that the required `code/`, `data/`, and `tests/` directories actually exist or contain any files; the claim cannot be verified from the given artifacts. The implementer must supply a directory listing or screenshots showing those three directories present in the repository.
- **T001c** — No evidence was provided that `.gitkeep` files exist in `data/raw`, `data/generated`, or `data/results`; the artifact list is empty, so the required files are missing.
- **T003** — I looked for the required linting and formatting configuration artifacts (e.g., a `ruff.toml`, `pyproject.toml` entries for Black, or a `.pre-commit-config.yaml` referencing these tools) but none were presented or referenced. Without concrete, non‑empty configuration files, the task of configuring ruff and Black is not demonstrated as completed.
- **T004** — No evidence of the required `data/raw`, `data/generated`, `data/results` directories or accompanying `.gitkeep` files is provided; without these artifacts the task’s requirement cannot be confirmed as satisfied.
- **T014a** — declared artifact(s) missing/empty/invalid: data/results/gradient_flow_log.json
- **T010b** — The required output file `data/raw/gam_reference_stats.json` is missing, so the mean/covariance statistics were never saved. The source data file exists, but without the resulting stats file the task is not fulfilled.
- **T018a** — declared artifact(s) missing/empty/invalid: data/results/trial_log.csv
- **T017** — The config file defines the timeout limits, but there is no evidence that the solver reads these limits, enforces a per‑step timeout, or writes timeout events (with `timeout=true` and `timeout_reason: step_limit`) to `data/results/trial_log.csv`. The CSV contains only a header and no recorded entries, and no code implementing the mechanism is provided. The task therefore remains unfinished.
