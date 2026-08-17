# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T031b` (rejected 1x): The provided `code/download/check_pilot_data.py` is truncated (ends with “impo”) and lacks the necessary imports, CSV loading, row‑count check, JSON output, and proper exit‑code handling; there is also no entry‑point (`if __name__ == "__main__":`). Consequently the script cannot fulfill the required behavior. The required data and schema files are also absent, but the primary issue is the incomplete implementation of the script itself.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

