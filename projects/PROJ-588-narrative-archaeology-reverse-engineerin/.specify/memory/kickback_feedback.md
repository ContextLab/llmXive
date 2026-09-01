# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): The provided `code/models/rsa.py` is truncated and never reaches the part that writes `results/rsa_matrices.json`; the JSON output file is absent. Consequently the required schema `{roi: {early_late: float, early_early: float}}` is not produced, and the implementation does not fully satisfy the task.
- `T024` (rejected 1x): The `code/utils/viz.py` file is truncated and the `plot_early_late_roi_comparison` function ends abruptly, indicating the visualization code is not fully implemented. Moreover, the required output file `results/rsa_heatmaps.png` does not exist. Both the functional artifact and the expected result are missing, so the task is not satisfied.
- `T031` (rejected 1x): No code, notebook, script, or output files implementing a 5‑fold cross‑validation and reporting accuracy versus a chance baseline are present. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

