# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/`, `results/`, `tests/`) is provided; the implementer did not supply a directory listing or any files showing that the project structure has been created.
- `T002` (rejected 1x): The provided material contains only a feature specification and user stories; there is no evidence of a Python 3.11 project being created (e.g., no `pyproject.toml`, `requirements.txt`, `setup.cfg`, or similar file) and none of the listed dependencies are declared or installed. Consequently, the task of initializing the project with the required packages has not been demonstrated.
- `T003` (rejected 1x): The implementer supplied only a feature specification for gene‑essentiality analysis and no linting/formatting configuration files, scripts, or documentation (e.g., `pyproject.toml`, `.ruff.toml`, Black config, or pre‑commit hooks). Consequently, the required artifacts for configuring ruff and black are missing.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: data/phylogeny/tree.newick
- `T017` (rejected 1x): The provided `code/main.py` is truncated and does not contain a complete orchestration loop that performs download → mapping → centrality → correlation → saving results. Moreover, the required output file `results/correlations.json` is absent. Both the core script and the expected result artifact are missing/incomplete.
- `T020` (rejected 1x): No code, tests, or documentation were provided showing that the pipeline now assigns a centrality of 0 for disconnected network components or that it logs a warning and skips organisms with no gene overlap. Without such artifacts, we cannot confirm the required error‑handling behavior was implemented.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

