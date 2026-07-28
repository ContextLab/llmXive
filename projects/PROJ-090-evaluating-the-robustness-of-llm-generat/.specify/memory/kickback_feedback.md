# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The required output file `data/processed/perturbation_candidates_raw.json` does not exist, so the pipeline’s persistence requirement cannot be verified. Moreover, the provided `generate_perturbations.py` is truncated and does not show the full logic for generating, scoring, and writing the candidates. Without the raw JSON file and complete implementation, the task is not satisfied.
- `T033` (rejected 1x): The repository lacks the required `data/processed/mixed_effects_results.json` file, and the provided tests write to a temporary location rather than the specified output path. Consequently the deliverable (a persistent JSON containing a positive variance component) is missing, so the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

