# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file list showing the required folders (`code/`, `tests/`, `data/`, `data/raw/`, `data/checkpoints/`, `data/results/`, `data/logs/`, `tests/unit/`, `tests/integration/`, `tests/contract/`) was provided. The evidence needed to confirm the project structure exists is missing.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or a `ruff` section, or a pre‑commit config invoking Black and Ruff) were provided, nor any evidence that these tools have been set up in the repository. The required artifacts are missing.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T018` (rejected 1x): No code, script, or documentation showing that the `memory_monitor` from T005 was integrated into the training loop, nor any evidence (e.g., logs, tests) that OOM conditions trigger an abort and checkpoint save. The required artifact is missing.
- `T019` (rejected 1x): No code, configuration, or log output showing added logging for wake/dream phase transitions, entropy metrics, or warm‑up status was provided; the claim lacks any concrete artifact to verify the required logging was implemented.
- `T025` (rejected 1x): No code, script, notebook, or output file was provided that computes the accuracy difference and performs the Wilcoxon signed‑rank test using `scipy.stats.wilcoxon` across the five seed accuracies. The required artifact (e.g., a function or report containing the computed difference and p‑value) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

