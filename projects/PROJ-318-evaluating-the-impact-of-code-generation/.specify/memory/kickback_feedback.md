# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings, screenshots, or command output were provided to demonstrate that the required folders (`code/`, `code/utils/`, `data/raw/`, `data/raw/repos/`, `data/processed/`, `tests/unit/`, `tests/integration/`, `state/`, `logs/`) actually exist; the claim is unsubstantiated. The implementer must supply concrete evidence (e.g., `ls -R` output, a script that checks each path, or a zip of the created structure).
- `T001b` (rejected 1x): No `.gitkeep` files were presented, and no output of the verification command (`find code data tests state logs -name .gitkeep | wc -l`) is provided to confirm that the count matches the number of newly created directories. The required artifact is missing.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

