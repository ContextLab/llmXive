# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): The provided `src/cli/train_predictor.py` is incomplete (the `save_model` function is truncated and never called) and the required output file `data/models/gap_predictor.pkl` does not exist. Consequently the script does not actually save a trained KRR model artifact as the task demands.
- `T027` (rejected 1x): The provided `run_baseline_sync.py` is truncated (e.g., an unfinished `else` clause) and does not contain the full logic to run inference, compute acceptance_rate, timing metadata, or write `data/processed/baseline_metrics.json`. Moreover, the required `baseline_metrics.json` file is missing entirely. The task therefore remains unfinished.
- `T029` (rejected 1x): The `src/utils/stats.py` file is truncated and does not contain a complete implementation of the paired t‑tests, Bonferroni correction, or JSON generation. Moreover, the required `data/processed/t_test_results.json` file is absent. Both the functional code and the expected output artifact are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

