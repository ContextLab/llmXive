# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No `tree_output.txt` (or any directory listing) was supplied, and there is no evidence that the required folder hierarchy was actually created under `projects/PROJ-044-evaluating-the-effectiveness-of-differen/`. Without this artifact the completion criterion cannot be verified.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- `T011` (rejected 1x): The required output files `data/raw/femnist.parquet` and `data/raw/femnist.sha256` are missing, so the task’s completion criterion is not satisfied. The downloader script exists but does not produce the needed files on disk.
- `T026` (rejected 1x): No evidence of a `results/plots/` directory or any PNG files (300 DPI) was provided; thus the required overlay plot of minority‑client degradation versus global accuracy curves is missing. The implementer must generate and supply the specified plot files in the correct location.
- `T029` (rejected 1x): No updated `README.md` or files under `docs/` were provided or referenced; the evidence contains only the feature specification and no documentation artifacts, so the required documentation updates are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

