# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The repository contains a partially shown `code/data/generator.py` but it does not include any logic that writes `data/processed/trajectories.json` or `data/processed/generation_stats.json`. Both required output files are absent from the filesystem, and the summary report with counts/percentages is not present. The task therefore remains unfinished.
- `T015` (rejected 1x): The required `data/processed/trajectories.json` file does not exist, so the output of exactly 500 unique trajectory IDs is missing. Moreover, the provided excerpt of `code/data/generator.py` does not demonstrate logic that enforces a 500‑trajectory count or raises an error if fewer are produced. Both the artifact and its behavior fail to meet the task’s specifications.
- `T019` (rejected 1x): The repository lacks the required `data/processed/classifier_training_data.json` file, and the provided `code/data/generator.py` snippet does not demonstrate the sliding‑window derivation, label string creation, or inclusion of `confidence_score` and `threshold_used` fields. Consequently the task’s output and schema requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

