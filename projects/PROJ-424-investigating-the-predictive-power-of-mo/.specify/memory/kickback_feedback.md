# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The core deliverable `data/raw/nist_refs.json` is MISSING (collector-confirmed), as is its `nist_refs.json.sha256` checksum file — so the curated reference data for water, ethanol, and acetone does not exist, and the loader/tests cannot pass (test_load_valid and test_checksum_matches would fail, and `load_refs()` would raise FileNotFoundError). The loader and test files themselves are well-formed, but without the actual data file and checksum the task's primary requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

