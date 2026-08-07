# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The claim provides only a textual description of feature specifications; no directory structure (code/, data/, tests/, docs/) or any files are shown or referenced. Without concrete evidence that these folders exist and contain content, the requirement to create the project structure is not satisfied. The missing artifact is the actual project hierarchy on disk.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8`) or any documentation/commands showing that ruff/flake8 and Black have been set up in the repository are present. Consequently the required artifact for task T003 is missing.
- `T016` (rejected 1x): No `data/synthetic/{seed}.json` file (or its contents) is presented, and there is no evidence that such a file exists or that its `sha256` field matches the hash of the generated dataset. The required artifact and verification are missing.
- `T017` (rejected 1x): No evidence of the required JSON files under `data/synthetic/trajectories/{seed}.json` was provided; without the actual trajectory files we cannot confirm that full p‑value trajectories are being stored as specified. The implementer must add the JSON output files (non‑empty) at the indicated location.
- `T021` (rejected 1x): No code, script, test output, or any other artifact demonstrating the implementation of the p‑value collection logic is present. Consequently there is no evidence that exactly $p$ p‑values are gathered per iteration, nor any verification that the implementation meets the specified user stories. The required implementation artifact and its validation results are missing.
- `T022` (rejected 1x): No code, script, or documentation was presented showing that `generate_data.py` was integrated and that hypothesis tests are automatically run on each generated dataset. The only material provided is a high‑level feature specification; there is no concrete artifact (e.g., modified `generate_data.py`, a new driver script, or test logs) to confirm the integration was implemented. The required integration artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

