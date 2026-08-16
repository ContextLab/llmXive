# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): No code, script, or log output was provided showing that rows with missing `effect_size` or `sample_size` are skipped, that zero‑variance fields are detected, or that warnings of the form `WARNING: Skipping row {index} due to {reason}` are emitted. The required error‑handling implementation and its logs are absent.
- `T015` (rejected 1x): The submission contains only the task description and project specifications; there is no code, script, log file, or any other artifact demonstrating that missing‑data rows are skipped, warnings are logged in the required format, or zero‑variance fields are handled. Consequently, the required error‑handling implementation and logging behavior are not evidenced.
- `T020` (rejected 1x): The provided `code/robustness.py` is truncated and the `run_permutation_test` function is not fully implemented (it ends abruptly with “required”). Moreover, the required output file `results/permutation_pvalue.json` and the input `results/lmm_final_summary.json` are absent, so the permutation test cannot be executed nor produce the specified JSON with `iterations_run` and `status`. The task therefore remains unfinished.
- `T023` (rejected 1x): No code, documentation, or test output was provided showing added logic to detect permutation convergence failures or to flag results as “approximate.” Without any artifact demonstrating this edge‑case handling, the task requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

