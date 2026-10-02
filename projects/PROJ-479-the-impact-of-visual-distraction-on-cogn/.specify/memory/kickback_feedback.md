# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T035` (rejected 1x): No code, script, or documentation was provided showing that the analysis pipeline was updated to apply `scipy.stats.multitest.multipletests(method='holm')`. The required artifact (an analysis script with Holm‑Bonferroni family‑wise error correction) is missing, so the task is not satisfied.
- `T036` (rejected 1x): The required `results/statistics/multiplicity_table.csv` file is missing, so the core output cannot be verified. Although the Holm‑Bonferroni citation is present in `data/citations.yaml`, there is no evidence that it was embedded in a report via T045. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

