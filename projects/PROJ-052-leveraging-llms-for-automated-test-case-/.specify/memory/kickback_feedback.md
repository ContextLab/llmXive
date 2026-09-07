# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T025` (rejected 1x): The repository lacks a complete implementation of `extract_changed_lines` in `code/data_loader.py` (the file ends abruptly and the function is not defined). Additionally, the required output file `data/changed_lines.json` does not exist. Both the core function and its expected artifact are missing, so the task is not satisfied.
- `T011a` (rejected 1x): No `main.py` file or any orchestration code is present, and there is no implementation that monitors cumulative execution time and enforces a hard stop when a predefined threshold is exceeded. The provided project specification concerns LLM test generation, coverage measurement, and statistical analysis, which does not address the required hard‑stop logic. The missing artifact is a functional `main.py` implementing the time‑threshold enforcement.
- `T011b` (rejected 1x): No `main.py` file (or any code) implementing the orchestration logic for a hard stop when the sample count reaches the configured limit is present. The provided artifacts relate only to LLM test generation and coverage reporting, not to the required `main.py` functionality. The missing implementation must be added and verified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

