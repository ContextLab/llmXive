# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/annotations/human_scores.csv, data/annotations/krippendorff_raw.json, data/results/validation_log.txt
- `T016` (rejected 1x): The provided `annotator.py` only logs errors and returns booleans; it does not raise exceptions when sample size is below 50 or when label independence fails. Moreover, the required `data/results/validation_log.txt` file is absent. Both the error‑raising behavior and the logging artifact are missing.
- `T035` (rejected 1x): The provided `code/eval/stats.py` stops after loading metrics and scores and never computes Pearson’s r, applies the required gating logic, or writes `proxy_validation.json`. Moreover, the expected output file `data/results/proxy_validation.json` does not exist. The task’s core functionality is missing.
- `T037` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/proxy_validation.json
- `T025` (rejected 1x): The repository contains `code/eval/stats.py`, but the shown portion does not include any function that runs a permutation test with `scipy.stats.permutation_test` nor writes a p‑value and gate status to `data/results/permutation_test.json`. Moreover, the expected output file `data/results/permutation_test.json` is absent. The task’s core requirement is therefore unmet.
- `T033a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/latency_raw.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

