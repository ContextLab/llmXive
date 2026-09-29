# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): The `code/scripts/baseline_cusum.py` file is present but its content is truncated (e.g., the `calculate_cusum_parameters` function ends abruptly) and there is no evidence that it writes a `data/results/cusum_predictions.csv` file (the CSV is missing). The required output artifact is absent, so the task is not fully satisfied.
- `T023` (rejected 1x): No artifacts (e.g., test logs, output files, verification scripts, or reports) were provided to demonstrate that baseline scripts T020‑T022 successfully read the unified data format from T004 and generated outputs compatible with evaluation script T026a. The claim lacks concrete evidence, so the integration verification cannot be confirmed.
- `T026b` (rejected 1x): The `code/scripts/sensitivity_analysis.py` file is present and appears to implement the threshold sweep, but the required output artifact `data/results/sensitivity_analysis.json` does not exist, and the script’s full implementation is truncated, so we cannot confirm it actually writes the JSON with false‑positive/negative rates. The missing JSON file means the task’s output requirement is not satisfied.
- `T028` (rejected 1x): The required image `paper/figures/fig1_timeseries.png` is absent, and the provided `render_fig1.py` script (truncated) does not show a `plt.savefig` call to actually write the figure to that path. The task’s core deliverable – the saved figure – is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

