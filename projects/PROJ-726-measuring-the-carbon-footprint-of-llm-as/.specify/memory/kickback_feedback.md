# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): No `run_inference.py` file or diff showing the inference loop wrapped in a `codecarbon.EmissionsTracker` configured for CPU is provided; without the actual code artifact we cannot confirm the required change was made. The implementer must supply the updated script (or a patch) demonstrating the tracker integration.
- `T013` (rejected 1x): No evidence of a modified `run_inference.py` was provided—there is no file content showing logging of CodeCarbon failures, skipping of the problematic prompt, or continuation of the loop. Without the actual script changes, the task’s requirement cannot be confirmed.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/llm_inference_results.json
- `T015` (rejected 1x): No code, script, or diff was provided showing that prompts which failed to generate code or produced empty strings are now filtered out before being written to the output file. The required validation logic is missing from the evidence, so the task is not demonstrably completed.
- `T019` (rejected 1x): No `calculate_emissions.py` file or code snippet showing LOC counting for the LLM‑generated code was provided. Without any artifact demonstrating that the implementation accesses `generated_code` strings and computes line counts, we cannot confirm the task was completed. The required functionality is missing from the evidence.
- `T020` (rejected 1x): No code changes or new functions in `calculate_emissions.py` are provided, nor any evidence (e.g., diff, snippet, test results) showing that line‑of‑code counting for LLM‑generated code was added or integrated with the raw code strings from T006/T016/T011. The required artifact is missing, so the task is not satisfied.
- `T021` (rejected 1x): No `calculate_emissions.py` file or any code implementing the human baseline CO₂ calculation is present; therefore the required artifact does not exist, and the task’s specification (using the mean of the reported time range and a standard laptop power model) cannot be verified. The implementer must add a functional script that performs this calculation.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

