# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): The provided `code/src/tracing.py` is truncated (ends mid‑function definition) and does not contain the full logic to load the model, iterate over images, enforce the memory guard, record routing matrices, or write the required `.npy` files. Moreover, the expected log files `data/results/tracing_log.jsonl` and `data/results/memory_profile_raw.jsonl` are absent. Consequently, the implementation does not meet the task specifications.
- `T012` (rejected 1x): The provided `clustering.py` does not show the required pure function `compute_canonical_map` nor any logic that saves `cluster_centers.json`; the JSON file is missing entirely. Consequently, the core functionality and output specified by the task are not present.
- `T013` (rejected 1x): The repository contains `code/src/canonical_map.py`, but the required output file `data/routing_cache/canonical_map.json` is absent, so the verification step (existence, correct schema, matching number of blocks) cannot be satisfied. The implementation also does not show code that writes the derived map to that JSON path. The missing JSON file must be generated for the task to be complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

