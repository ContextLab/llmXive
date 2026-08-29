# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T045` (rejected 1x): The `code/03_diversity.py` file does not contain any PERMANOVA logic (it ends abruptly with a typo and no pairwise testing), and the required output file `data/processed/permanova_pairwise_matrix.json` is absent. The task’s core functionality and output are therefore missing.
- `T047` (rejected 1x): The provided `code/99_generate_final_report.py` is incomplete (truncated mid‑function, no code that writes `final_analysis_report.json`). Moreover, the required output file `data/processed/final_analysis_report.json` does not exist. The task’s core deliverable—a merged JSON report with a data_lineage section—is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

