# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008a` (rejected 1x): The `code/imbalance.py` file exists but its visible portion does not show the required logic for filtering properties with ≥ 100 samples, handling negative values, computing the Gini coefficient, and writing the results to `results/target_imbalance_scores.csv`. Moreover, the expected output CSV file is missing from the repository. The implementer must add the missing functionality and generate the CSV file.
- `T008b` (rejected 1x): The provided `code/imbalance.py` is truncated and never performs the required K‑Means clustering (k=50), counts cluster assignments, computes the Gini coefficient, or writes `results/compositional_imbalance_score.csv`. Moreover, the input file `data/processed/descriptors.parquet` and the expected output CSV are absent. The task’s core functionality and artifacts are therefore not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

