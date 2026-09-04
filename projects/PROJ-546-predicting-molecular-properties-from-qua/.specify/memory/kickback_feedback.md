# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): The repository lacks the required `data/raw/barrier_dataset.csv`, and consequently `data/confounds.csv` and `data/confounds_verification.log` are absent. Moreover, `code/confounds.py` is truncated (e.g., `calculate_molecular_properties` ends with an unfinished line) and does not contain the logic to write the output CSV or perform the verification logging. The implementation is therefore incomplete.
- `T020a` (rejected 1x): The repository lacks `data/raw/barrier_dataset.csv` and `data/confounds.csv`, so the dependency check cannot pass. Moreover, `code/dft_calculator.py` contains DFT execution code but does not implement the required subset‑selection logic (reading the barrier dataset, computing N, stratified qcut binning, and selecting 50 or fewer samples). These core pieces are missing.
- `T022` (rejected 1x): The required output file `reports/evaluation.json` does not exist, so the script’s results are not materialized. Additionally, the provided `code/evaluate_models.py` is truncated and does not show the full implementation of per‑fold MAE computation, paired t‑test, or MAE flag logic, making it unclear that the script meets the specification. The missing JSON report must be generated with the specified keys for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

