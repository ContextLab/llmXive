# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012a` (rejected 1x): The required data files (`full_splits.json`, `unseen_validation_set.csv`, `exclusion_log.json`, `entropy_results.csv`) are absent, and the provided `entropy.py` contains placeholder logic (random sample generation, ignores the CSV reference, missing imports, truncated code) that does not fulfill the specified processing, clustering, entropy calculation, or logging requirements.
- `T013b` (rejected 1x): The required input file `data/processed/full_splits.json` and the output file `data/processed/convergence_results_sensitivity.csv` are both missing, so the inference step for k=4 was never executed and no results were saved. The task therefore is not satisfied.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/router_cv_folds.json
- `T019b` (rejected 1x): The required output file `data/processed/router_results.csv` is absent, and the necessary inputs `data/processed/router_model.pkl` and `data/processed/full_splits.json` are also missing, so the router predictions cannot have been generated.
- `T021c` (rejected 1x): The required `data/processed/config.json` file is missing, so the extracted `NON_INFERIORITY_DELTA` and `RANDOM_SEED` have not been written to the expected location. The implementer must create the JSON file containing those two values.
- `T020a` (rejected 1x): The required input file `data/processed/convergence_results_core.csv` is absent, and the expected output `data/processed/static_k2_baseline.json` was not generated. Consequently the FLOPs/accuracy baseline cannot have been computed as specified.
- `T025a` (rejected 1x): No `stratum_pvalues_powered.json` file or any other output artifact was presented. Without the required JSON containing the per‑stratum powered‑only p‑values, the task’s deliverable is missing. The implementer must generate and provide this file.
- `T025c` (rejected 1x): The claim provides no actual `convergence_results_merged.csv` file (or any CSV) to inspect, and there is no evidence that the two source CSVs were concatenated. Without the merged file present and verified, the task requirement is not satisfied.
- `T026` (rejected 1x): The required input `data/processed/convergence_results_merged.csv` does not exist, and the expected output `data/processed/sensitivity_sweep.json` was not generated. Without the input CSV the analysis script cannot compute the Spearman correlations, so the task’s deliverable is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

