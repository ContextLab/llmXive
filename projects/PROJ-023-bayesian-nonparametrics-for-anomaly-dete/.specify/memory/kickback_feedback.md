# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): The `code/scripts/baseline_cusum.py` file exists, but the required output file `data/results/cusum_predictions.csv` is missing, so the script’s primary deliverable has not been produced. The task is therefore not fully satisfied.
- `T022` (rejected 1x): The provided `baseline_vae.py` is incomplete (truncated mid‑function and never reaches inference or CSV writing) and does not use the required `scikit-learn` or `pytorch‑lightning` libraries. Moreover, the expected output file `data/results/vae_predictions.csv` is absent.
- `T023` (rejected 1x): No code, scripts, or documentation showing that the baseline algorithms have been wired into the shared data loader and anomaly‑injection pipeline is present. The required integration artifact is missing, so the task is not satisfied.
- `T027` (rejected 1x): The provided `sensitivity_analysis.py` is present but appears truncated and does not show any logic that sweeps thresholds or writes the required `data/results/sensitivity_analysis.json`. Moreover, the JSON output file is missing from the repository. The implementation must include the threshold‑sweep computation and generate the JSON report at the specified path.
- `T028` (rejected 1x): The required figure `paper/figures/fig1_timeseries.png` does not exist, and the provided `render_fig1.py` is truncated (no visible code that actually saves the plot to the specified path). Without a generated PNG at the correct location, the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

