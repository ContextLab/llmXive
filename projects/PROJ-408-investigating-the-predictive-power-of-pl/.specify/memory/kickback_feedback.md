# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002a` (rejected 1x): No script, log, or command output showing that `mafft` and `fasttree` were installed (e.g., an `apt-get install` command) and subsequently verified to be in the system `PATH` is present. Without such evidence, we cannot confirm the binaries are installed and discoverable, so the task requirement is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., ruff, flake8, black) are present, and there is no evidence that specific error codes for unused imports or missing type hints are being enforced. The required artifact (tool configuration) is missing.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: code/validate_env.py
- `T011` (rejected 1x): The required output file `data/processed/test_tree.newick` is missing, and there is no evidence of a Mantel test result or p‑value assertion being performed. Without the generated tree (and associated statistical output), the integration test cannot be considered completed.
- `T012` (rejected 1x): No actual artifact (e.g., script, output file, correlation value, or report) was provided showing that shuffled metabolite profiles were tested and yielded a correlation |r| < 0.05. The claim lacks any concrete evidence, so the requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

