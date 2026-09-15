# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): No code, script, log file, or measurement output was provided to demonstrate that memory usage is monitored and stays below the 6.5 GB peak RSS limit during sequential subject processing. The required artifact (e.g., a monitoring implementation or benchmark results) is missing.
- `T019` (rejected 1x): No epoch files or saving script were presented in the evidence; the required `data/processed/` directory with per‑subject clean epoch objects (and the hashing step from T004) is missing, so the task’s deliverable cannot be confirmed.
- `T023` (rejected 1x): No code, script, or other artifact implementing the theta (‑7 Hz) and gamma (‑45 Hz) band‑pass filters was provided; the evidence consists only of the task description, which does not contain the required implementation. Consequently the required filtering functionality cannot be verified as present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

