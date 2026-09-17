# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T050` (rejected 1x): No code, documentation, or test artifacts showing that T006 now contains the streaming download and chunked processing logic required by T050 are provided. Without concrete evidence of the merged implementation, the claim cannot be verified. The next implementer should supply the relevant source files (e.g., the updated T006 module) and/or a description demonstrating the required functionality.
- `T018b` (rejected 1x): The repository does not contain a `log_fallback_prompt_usage` function in `code/data_loader.py` (the provided excerpt shows no such implementation), and the required `data/metrics.json` file is absent. Consequently, the task of recording a warning and updating the fallback prompt count metric has not been fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

