# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`data/raw`, `data/processed`, `code`, `figures`, `analysis`, `contracts`) is provided; the claim lacks any artifact confirming the project structure was created.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, pre‑commit hooks, or related scripts) are present in the provided evidence, so the requirement to configure Ruff and Black is not satisfied.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T014** — No filtering script, module, or log files were provided; there is no evidence of implemented logic that excludes non‑sequential or non‑predictable datasets nor of any logged exclusion reasons. The required artifact is missing, so the task is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/standardized.csv
- **T017b** — No files or directories were presented showing that the required “transition‑probability tables” and “Markov model state” have been saved under `data/processed/`. The evidence is missing, so the task’s artifact requirement is not satisfied.
- **T022** — No code, script, or documentation was provided that shows a convergence check for the mixed‑effects model or a fallback to a random‑intercept‑only model when convergence fails. The required implementation and any associated tests or examples are missing.
- **T023** — No code, script, or module implementing Bonferroni or Benjamini‑Hochberg correction (with the required `num_tests > 1` guard) was presented. The artifact is missing, so the task’s requirement is not satisfied.
- **T023b** — No code, script, or configuration implementing the FWER verification logic was presented, nor any `analysis/results.json` file containing a `fwer_control_status` entry. The required artifact is missing, so the task is not satisfied.
