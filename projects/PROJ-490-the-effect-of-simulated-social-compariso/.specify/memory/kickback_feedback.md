# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T011` (rejected 1x): No code, configuration, or documentation was provided showing a fallback mechanism that detects missing real data, invokes a synthetic data generator, and sets a `data_source_type` flag as required by FR‑009. The evidence consists only of the task description and project spec, without any concrete implementation artifact. The missing artifact is the actual implementation (e.g., a script, function, or pipeline component) that performs this logic and records the flag.
- `T013` (rejected 1x): No code, script, test, or documentation was presented that adds a check for the presence of the four required variables in `data/raw`. Consequently, there is no artifact confirming that the validation step exists or functions as specified. The implementer must provide the actual implementation (e.g., a Python function, CI test, or documentation) that verifies the presence of `avatar_condition`, `pre_self_esteem`, `post_self_esteem`, and `comparison_tendency` before the pipeline proceeds.
- `T020` (rejected 1x): No code, configuration, or documentation implementing the required dynamic interpretation logic (“Empirical Association” for real data vs “Simulated Causal Effect” for synthetic data) was provided. The response contains only the task description and acceptance criteria, but no actual artifact (e.g., a function, module, or test) that demonstrates the logic is present. The implementer must supply the concrete implementation and evidence (e.g., source file, unit test, or usage example) showing the logic works as specified.
- `T021` (rejected 1x): No CSV file with regression coefficients nor a JSON file with diagnostics (p‑values, VIF, confidence intervals) was presented in `data/processed/`. The claim lacks any concrete artifacts to verify that the required outputs were generated. The next implementer must create and provide the non‑empty CSV and JSON files in the specified directory.
- `T022` (rejected 1x): The implementer provided no code, analysis report, or documentation showing that VIF values ≥ 5 are detected, flagged, and that the results are described without asserting independent effects. Without any artifact demonstrating this collinearity handling, the task requirement is unmet. The next implementer must supply the analysis script (or notebook) and the resulting output (e.g., a table of VIFs with flags and a written interpretation) that explicitly addresses the VIF ≥ 5 scenario.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

