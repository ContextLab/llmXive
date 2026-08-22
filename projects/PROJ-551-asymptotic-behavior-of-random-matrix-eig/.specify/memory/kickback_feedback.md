# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019a` (rejected 1x): No NumPy code or saved `.npy` files were presented; the required `data/raw/matrix_N{N}_seed{seed}.npy` files do not exist in the provided evidence, so the task of generating and persisting raw Wigner matrices is not demonstrated.
- `T019` (rejected 1x): The required output file `state/checksums_raw.json` does not appear in the provided evidence, and no SHA‑256 checksums of the raw matrix instances are present. Consequently the task’s core requirement—generating and recording those checksums—is not satisfied.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/single_run_results.json
- `T040a` (rejected 1x): No files were found in the repository at the required path `data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy`, and no code or logs were provided that generate such raw matrix instances. Consequently the task’s deliverable – the full set of raw matrix `.npy` files for the parameter sweep – is missing.
- `T040b` (rejected 1x): No `state/checksums_sweep.json` file or any other evidence of computed SHA‑256 checksums for the raw matrix instances from T040a is present. The required artifact is missing, so the task is not satisfied.
- `T021a` (rejected 1x): The repository contains `code/analysis/monte_carlo_runner.py`, but the provided snippet is truncated and does not show any code that writes results to `data/processed/mc_results.csv`. Moreover, the required CSV file is absent from the project. Without a concrete implementation that outputs the specified schema and the actual CSV file, the task is not fulfilled.
- `T021b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/mc_results.csv, data/processed/threshold_identification_raw.json
- `T022c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/threshold_fit_params.json
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/threshold_sweep_results.csv
- `T025` (rejected 1x): declared artifact(s) missing/empty/invalid: data/figures/outlier_probability_vs_theta.png
- `T031` (rejected 1x): declared artifact(s) missing/empty/invalid: data/logs/edge_case_rank0.log

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

