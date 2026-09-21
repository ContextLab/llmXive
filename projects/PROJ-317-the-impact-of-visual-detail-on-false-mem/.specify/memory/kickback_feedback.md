# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The repository contains `code/stimuli/metadata.py`, but the file is truncated and never writes any YAML files to `data/stimuli/`. No `data/stimuli/{id}_metadata.yaml` files are present (the only referenced `_metadata.yaml` is missing). Consequently the required output files and full metadata generation logic are not provided.
- `T035#1` (rejected 1x): The repository contains `code/analysis/anova.py` with a gate check and ANOVA computation, but the script does not show any code that writes the results to `data/analysis/anova_results.json`, and that JSON file is missing. Consequently the required output artifact and schema verification are not satisfied.
- `T096` (rejected 1x): No `plan.md` file or its contents were provided; consequently we cannot verify that it contains the required phrases “ladder of explanation” and “serotonin → cAMP → PKA → CREB”. The implementer must supply the updated `plan.md` with the specified subsection and verify the phrases are present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

