# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010#1` (rejected 1x): The repository contains `code/download_encode.py`, but the required output files `data/raw/encode_counts.csv` and `data/raw/encode_peaks.bed` are absent, and no checksum file is present. Without these data artifacts the task’s deliverables are not satisfied.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/synthetic_counts.csv, data/raw/synthetic_peaks.bed
- `T013` (rejected 1x): The repository lacks the required `data/processed/merged_matrix.csv` input and does not contain the expected `data/processed/filtered_expression.csv` output. Although `code/preprocess.py` defines filtering and log‑pseudocount functions, there is no script or entry point that reads the input, applies these steps, and writes the deliverable file. The task therefore remains unfinished.
- `T016` (rejected 1x): The repository lacks the required input `data/processed/imputed_expression.csv` and the output `data/processed/housekeeping_genes.csv`. Moreover, `code/preprocess.py` does not contain any implementation that computes the coefficient of variation, applies the default CV < 0.2 threshold, or writes the housekeeping genes file, and the file is truncated before such logic could appear. The task is therefore not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

