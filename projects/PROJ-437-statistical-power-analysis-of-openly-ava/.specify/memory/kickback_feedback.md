# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): The repository contains a partially‑implemented `glm_fitter.py` (the file is truncated and does not show code for loading real preprocessed data, random subject subsampling, computing Cohen’s d, or writing the required JSON log). Moreover, the expected output file `data/aggregated/convergence_log.json` is absent. These missing pieces mean the task’s core requirements are not satisfied.
- `T019` (rejected 1x): No updated `split_half_validator.py` file or code snippet is provided; thus there is no evidence that the validator was extended to discard non‑convergent GLM iterations or to flag runs as “Unreliable” when more than 20 % of iterations fail. The required artifact is missing.
- `T023` (rejected 1x): No code artifact (e.g., an updated `power_curve_generator.py` containing the required clamping logic for Edge Case 2) was provided; the evidence section contains no files or snippets to inspect. Consequently, we cannot confirm that the requested sample‑size‑clamping behavior was implemented. The missing artifact must be added and its functionality demonstrated.
- `T024` (rejected 1x): No `power_curve_generator.py` file (or any code) containing a logistic regression model with the specified fixed effects and alpha‑sweep logic is present. The required artifact is missing, so the task’s requirements have not been satisfied.
- `T025` (rejected 1x): No `power_curve_generator.py` file or code changes were provided, and there is no evidence of VIF calculation, logging of “High Collinearity”, or metadata flagging of “Invalid”. The required artifact is missing, so the task is not satisfied.
- `T031` (rejected 1x): No modified `power_curve_generator.py` (or any code, script, or output) is provided; the claim lacks the required artifact that implements separate loops for the 4 s and 8 s temporal smoothing kernels and produces per‑kernel power curves. The task therefore remains undone.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

