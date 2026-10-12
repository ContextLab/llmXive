# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The directory tree itself was created (all listed `src/`, `data/`, `output/`, `contracts/` subdirectories exist), and the setup script's execution log claims a snapshot was captured. However, the collector's evidence contains no `logs/` directory and no `logs/structure.txt` file — the required verification artifact (non-empty, containing a line per listed directory) is absent, so the grep verification cannot be confirmed. The implementer must ensure `logs/structure.txt` actually exists on disk (and that `logs/` is present) with the `tree -a -L 3` output.
- `T003` (rejected 1x): Requested task execution failed; rerun successfully: code/run_lint.py exit=1

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

