# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`data/raw`, `data/processed`, `code`, `figures`, `analysis`, `contracts`) is provided; the claim lacks any artifact confirming the project structure was created.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, pre‑commit hooks, or related scripts) are present in the provided evidence, so the requirement to configure Ruff and Black is not satisfied.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T014` (rejected 1x): No filtering script, module, or log files were provided; there is no evidence of implemented logic that excludes non‑sequential or non‑predictable datasets nor of any logged exclusion reasons. The required artifact is missing, so the task is not satisfied.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/standardized.csv
- `T017b` (rejected 1x): No files or directories were presented showing that the required “transition‑probability tables” and “Markov model state” have been saved under `data/processed/`. The evidence is missing, so the task’s artifact requirement is not satisfied.
- `T022` (rejected 1x): No code, script, or documentation was provided that shows a convergence check for the mixed‑effects model or a fallback to a random‑intercept‑only model when convergence fails. The required implementation and any associated tests or examples are missing.
- `T023` (rejected 1x): No code, script, or module implementing Bonferroni or Benjamini‑Hochberg correction (with the required `num_tests > 1` guard) was presented. The artifact is missing, so the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

