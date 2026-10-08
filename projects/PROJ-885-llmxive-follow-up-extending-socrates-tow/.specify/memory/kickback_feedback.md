# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T027` (rejected 1x): The runner.py file only contains a helper `enforce_cpu_only_execution` but does not show the required transformers inference loop, explicit CPU device mapping, bitsandbytes/quantization exclusion, or low‑confidence neutral‑state fallback. Moreover, the required `data/results/scope_adjustments.json` file is absent, so the exclusion‑record requirement cannot be verified. The implementer must add the full CPU‑only inference implementation and ensure the JSON file is created/updated as specified.
- `T013` (rejected 1x): The repository lacks the required `data/processed/generation_stats.json` file, and the provided `code/data/generator.py` snippet shows no implemented oversampling logic or code that writes the requested `oversampling_ratio` and `high_emotion_count` values. Both the artifact and the required output are missing.
- `T014` (rejected 1x): The repository lacks the required output files `data/processed/trajectories.json` and `data/processed/generation_stats.json`. Moreover, the provided `code/data/generator.py` is truncated and shows no implementation of writing trajectories or generating the summary report with the specified schema. The task’s core output artifacts are therefore missing.
- `T015` (rejected 1x): The repository lacks the required output files `data/processed/trajectories.json` and `data/processed/generation_stats.json`, and the provided `code/data/generator.py` is truncated and shows no logic that writes those files or sets `underpowered_flag` when the count is below 500. Consequently the task’s core requirements are not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

