# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The provided `clustering.py` is only partially shown and does not contain the full logic for silhouette computation, null‑hypothesis handling, writing `null_hypothesis_flag.json`, or saving `cluster_centers.json`. Moreover, the required output files `data/results/null_hypothesis_flag.json` and `data/routing_cache/cluster_centers.json` are missing. The implementation must be completed to meet all specified behaviors.
- `T013` (rejected 1x): The repository contains `code/src/canonical_map.py`, but the required output file `data/routing_cache/canonical_map.json` does not exist, so the verification condition (file existence and correct dict structure) is not met. The implementer must generate and save the canonical map JSON at the specified location.
- `T018` (rejected 1x): The repository contains a `static_model.py` file, but it is truncated (ends mid‑method) and does not provide a complete implementation that removes the dynamic softmax computation. Moreover, the required `data/routing_cache/canonical_map.json` file is absent, so the model cannot even be instantiated as specified. Both the code and the necessary data artifact are missing/incomplete.
- `T026` (rejected 1x): declared artifact(s) missing/empty/invalid: src/stats_analysis.py, data/results/statistical_analysis.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

