# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): The required `data/raw/checksum.txt` file does not exist, and the provided `loader.py` snippet is truncated so it’s unclear whether it writes the checksum in the exact “sha256: <hex_string>” plain‑text format or triggers the Verified Accuracy Gate on failure. The missing checksum file alone means the task’s output requirement is not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

