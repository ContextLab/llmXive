# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017a` (rejected 1x): The provided `src/data/process.py` contains chess‑related utilities but no code that computes `total_games`, `parsed_games`, calculates `inclusion_rate`, or writes `data/results/inclusion_metrics.json`. Moreover, the required JSON file is absent from the repository. The task’s core output is therefore missing.
- `T017b` (rejected 1x): The provided `src/data/process.py` contains chess‑related utilities but does not include any code that reads `data/results/inclusion_metrics.json` or checks an `inclusion_rate` against the 0.95 threshold. Moreover, the required `data/results/inclusion_metrics.json` file is absent from the repository. Both the validation implementation and the input file are missing, so the task is not satisfied.
- `T018` (rejected 1x): The provided `src/main.py` is truncated and never calls the validation function nor writes the final `games.parquet` file; the required `data/processed/games.parquet` is missing. The script therefore does not meet the specification of exiting with code 0 after successful validation and producing the parquet output. The implementation must be completed to perform validation and save the dataset to the expected location.
- `T021a` (rejected 1x): The required `data/processed/eco_mapping.json` file is missing, and the `src/models/fit.py` mapping (`ECO_FAMILIES`) does not follow the specified deterministic dictionary (e.g., it uses “Flank Openings” instead of “King's Pawn”, etc.). Consequently the task’s deliverables are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

