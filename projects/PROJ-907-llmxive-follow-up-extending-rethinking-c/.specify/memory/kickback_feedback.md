# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The provided `clustering.py` is truncated and does not contain code that saves cluster centers to `data/routing_cache/cluster_centers.json`, prints the silhouette score, or implements the null‑hypothesis fallback. Moreover, the required `cluster_centers.json` file is missing entirely. The task’s core output is therefore not present.
- `T013` (rejected 1x): The repository contains `code/src/canonical_map.py`, but the required output file `data/routing_cache/canonical_map.json` is missing, so the verification step cannot be satisfied. The implementation has not produced the expected JSON artifact.
- `T018` (rejected 1x): The repository contains a `static_model.py` file, but the implementation is truncated, has an unfinished `get_static_routing_weight` method, and never loads the required `data/routing_cache/canonical_map.json`. Moreover, the `canonical_map.json` file itself is missing, so the model cannot be instantiated with the static routing map as required.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

