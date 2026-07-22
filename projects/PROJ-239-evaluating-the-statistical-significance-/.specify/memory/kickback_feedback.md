# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T035` (rejected 1x): The repository contains `code/synthetic_cluster_params.py` with the hard‑coded statistics and a function that generates log‑normal cluster sizes, but the script excerpt stops before any validation against `ICC_RANGE` or saving of the generated list to `data/derived/synthetic_cluster_structure.csv`. Moreover, the required CSV file is absent. The deliverable therefore does not fully satisfy the task’s validation and output requirements.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

