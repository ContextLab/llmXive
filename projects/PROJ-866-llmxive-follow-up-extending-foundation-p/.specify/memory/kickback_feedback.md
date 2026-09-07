# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): No code artifact (e.g., a modified `full_context.py` file) or execution‑log example was provided showing the new handling for single‑node graphs with `depth=0`, nor evidence that `context_reduction_pct` is set to the string `'[deferred]'` and `status` to `'edge_case'`. The required implementation and its verification are missing.
- `T032` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/tradeoff_curve.csv
- `T017` (rejected 1x): No code, script, test, or documentation for a filter that detects and excludes “invalid workflows” is present; the claim cannot be verified against any artifact. The required implementation artifact is missing.
- `T018` (rejected 1x): No evidence of a `state/projects/PROJ-866-...yaml` file containing checksums for the workflows in `data/raw/` was provided; the response contains only the task description and no actual artifact or its contents. The required registry update is therefore not demonstrated.
- `T023` (rejected 1x): No `main.py` file or any code implementing batch execution across multiple compression levels was provided; the only evidence is the feature specification text, which does not demonstrate that the required logic exists or is functional. The implementer must add the actual `main.py` implementation (or show the relevant code) that runs a large number of workflows for various compression settings.
- `T024` (rejected 1x): No code, logs, or documentation were provided showing that the system actually records a specific “policy‑violation” entry when a truncation cuts off required nodes such as data‑sovereignty rules. The required artifact (implementation and/or example log output) is missing.
- `T025` (rejected 1x): No files or code were presented that create or store processed execution logs in `data/processed/`, nor any evidence that those logs contain the required fields (compression level, token count, violation flags). The artifact required by the task is missing.
- `T026` (rejected 1x): No code, tests, or documentation showing that the system now handles a compression depth of 0 without error is present; the only evidence is the task description, which does not include any implementation artifact. The required logic and its verification are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

