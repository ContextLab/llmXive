# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: stats_config.yaml
- `T005` (rejected 1x): No `roi_masks/auditory_cortex.nii.gz` file or script showing the use of `nilearn.datasets.fetch_atlas_harvard_oxford` to extract the Auditory Cortex label is present. The required ROI mask artifact is missing, so the task is not satisfied.
- `T008` (rejected 1x): No script, Dockerfile, or configuration file was provided that pulls `nipreps/fmriprep` with a specific stable version tag. The required artifact is missing, so the task’s requirement is not satisfied.
- `T009` (rejected 1x): No `spec.md` file or its contents were provided, so there is no evidence that the required text replacement (“ds000115” → “ds000246” in FR‑001, User Story 1, and Assumptions) was actually made. The implementer must supply the updated `spec.md` showing the changes.
- `T010` (rejected 1x): No updated `spec.md` file is provided, and there is no evidence that the phrase “paired-sample t-test” was replaced with “one-sample t-test against zero” in FR‑004. The required artifact (the modified specification document) is missing.
- `T011` (rejected 1x): No updated `spec.md` file is provided, so we cannot confirm that FR‑005’s wording was changed from “per condition” to “global (independent of condition)”. The required artifact (the modified specification document) is missing.
- `T012` (rejected 1x): No updated `spec.md` file is provided, and there is no evidence that the text “p < 0.05” in SC‑002 was replaced with “p < 0.10”. The required artifact (the modified specification document) is missing.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/preprocessing.log

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

