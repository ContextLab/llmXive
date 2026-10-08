# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The provided `preprocess.py` defines helper functions (`load_schema`, `validate_schema`) but the file is truncated before the implementation of `validate_schema` and there is no code shown that calls `jsonschema.validate` on the filtered DataFrame. Consequently, we cannot confirm that the schema is loaded and validation is performed after filtering, as required. The task needs a concrete call to `jsonschema.validate` (or equivalent) on the filtered data.
- `T026` (rejected 1x): The `code/data/compute_metrics.py` shown does not contain any code that logs a “CONVERGENCE: X% success, Y failed fits” message nor writes aggregated statistics to `results/convergence_stats.json`. Moreover, the required `results/convergence_stats.json` file is absent from the repository. The task’s core output is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

