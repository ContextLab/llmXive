# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): No preprocessing script, configuration, or generated epoched data files are present in `data/processed/`. The required implementation (band‑pass, notch, bad‑channel interpolation, ICA cleaning, and 2‑second epoching) and its output are missing, so the task is not satisfied.
- `T015` (rejected 1x): The provided `code/compute_entropy.py` contains placeholder logic (e.g., hard‑coded entropy values, truncated code, no CSV writing) and does not actually compute or save Sample and Approximate Entropy for the five bands. Moreover, the required output file `data/processed/entropy_metrics.csv` is absent. The implementation therefore fails to meet the task’s functional requirements.
- `T017` (rejected 1x): No evidence of the required `logs/resource_usage.log` file or of added resource‑monitoring calls in `02_preprocess_eeg.py` and `03_compute_entropy.py` was provided; without these artifacts we cannot verify that RAM usage is limited to <7 GB. The implementer must supply the modified scripts and the generated log file.
- `T018` (rejected 1x): The test file `tests/contract/test_correlation_schema.py` is present, but the required schema file `correlation_results.schema.yaml` does not exist in the repository, causing the test to fail (it checks for the schema’s existence). The missing schema means the contract test cannot be validated, so the task is not fully satisfied.
- `T020a` (rejected 1x): The repository contains a partially written `code/04_regression_analysis.py` that stops mid‑implementation and never performs the OLS regression or writes the required `data/processed/correlation_results_ols.csv`. Moreover, the expected output CSV is absent from the `data/processed` directory. The task’s core requirement—running the multiple linear regression with the specified covariates and producing the results file—is therefore not satisfied.
- `T021` (rejected 1x): The repository lacks the required `data/processed/correlation_results_ols.csv` and the resulting `data/processed/correlation_results_fdr.csv`, so the pipeline cannot be run or verified. Moreover, the provided `code/04_regression_analysis.py` is truncated and does not contain the full implementation of VIF checking, conditional dropping of Approximate Entropy, re‑running OLS, or writing the FDR‑corrected results. Both the necessary data files and a complete script are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

