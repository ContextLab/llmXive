# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): No evidence of the required `data/raw/` and `data/processed/` directories or accompanying `.gitkeep` files is provided; the artifact list is empty, so the task’s deliverable cannot be confirmed. The implementer must add the two directories with a `.gitkeep` file in each.
- `T043` (rejected 1x): No updated README.md or docs/ files were provided; the only evidence shown relates to feature specifications, not to any documentation changes. The required documentation artifacts are missing.
- `T044` (rejected 1x): No code files, diff, or documentation were presented showing any cleanup or refactoring in the `code/` directory, and the provided specification concerns data simulation and analysis rather than code maintenance. Consequently, there is no evidence that the required cleanup work was performed.
- `T047` (rejected 1x): No evidence of any new files or content under `tests/unit/` was provided; the claim that additional unit tests were added cannot be verified. The required artifact (the added unit test code) is missing.
- `T048` (rejected 1x): No evidence of a quickstart.md validation run (e.g., execution logs, validation report, or updated documentation) is provided; the required artifact is missing, so the task is not satisfied.
- `T049` (rejected 1x): No reproducibility artifacts (e.g., a script that re‑runs the entire pipeline with fixed random seeds, logs of the run, and checksum files for outputs) were supplied; the claim provides only the original feature specification, not the required re‑run and checksum comparison evidence.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

