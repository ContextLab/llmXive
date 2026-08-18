# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T038b` (rejected 1x): No monitoring script (`utils/monitor.py`) or modifications to `run_experiment.py` are provided, nor any log or measurement showing that peak RAM usage stays below 6.5 GB. The required artifact and proof of the RAM bound are missing.
- `T040` (rejected 1x): No updated versions of `download_micro_corpus.py` or `split_data.py` are provided, nor any diff, test, or description showing that input validation and path sanitization were added. The evidence consists only of a high‑level feature specification, which does not demonstrate that the required security hardening was implemented. The implementer must supply the modified scripts (or a clear patch) that include the new validation and sanitization logic.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

