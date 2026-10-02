# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The required output file `data/interim/background_union.bed` does not exist, and the provided `code/preprocess.py` is truncated and shows no evidence of actually performing the aggregation and writing that file. Without the generated BED file, the task’s core requirement is unmet.
- `T015` (rejected 1x): The repository lacks the required `data/processed/ingestion_summary.json` file, and the `run_ingestion` implementation does not match the specification: it has no `peak_files` parameter, does not enforce the exact cell‑type list `['GM12878', 'K562', 'HepG2', 'H1‑hESC', 'IMR90']`, and does not raise an error for unexpected types. The generated summary also uses dynamic keys rather than the mandated exact values.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

