# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The repository lacks the required `data/processed/raw_metrics.json` file (the processor never created it) and the schema file `contracts/output.schema.yaml` is absent, so the output cannot be validated against the specified schema. Additionally, the provided `processor.py` is truncated, leaving uncertainty that it fully implements the waiting, filtering, timing, and efficiency‑reporting steps. These missing artifacts prevent the task from being considered complete.
- `T022` (rejected 1x): The repository contains `code/llm/pipeline.py`, but the file is truncated and does not show the full implementation (e.g., the loop body is cut off). More critically, the required output artifact `data/processed/refactoring_results.json` is absent, so the pipeline does not actually save the deltas as specified. The missing result file must be generated for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

