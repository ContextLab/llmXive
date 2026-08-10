# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T051` (rejected 1x): The provided `code/data/external.py` is truncated before the GitHub/NPM request logic, so we cannot verify that the functions actually use the cache or respect the 24‑hour TTL. Additionally, the required cache file `data/cache/github_api_cache.json` does not exist on disk. The implementation must be shown in full and demonstrate writing/reading the cache file to satisfy the task.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

