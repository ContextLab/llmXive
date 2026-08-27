# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T022` (rejected 1x): The repository contains the `code/04_apply_fdr.sh` script, but it is truncated at the end and the required output file `data/processed/gwas_results_fdr.tsv` does not exist. The task demands both the script **and** the generated final artifact, which are missing/incomplete. The next implementer must fix the script (ensure it finishes correctly) and run it (or otherwise provide the merged `gwas_results_fdr.tsv` file).

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

