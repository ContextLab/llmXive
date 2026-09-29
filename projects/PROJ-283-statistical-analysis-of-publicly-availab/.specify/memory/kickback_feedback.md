# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): The `src/data/parse.py` file contains only imports and a `pass` statement—no `parse_pgn_stream` implementation or any logic to produce `GameRecord` objects. Additionally, the required `src/data/models.py` (defining the `GameRecord` TypedDict) and the schema file `specs/contracts/game_record.schema.yaml` are missing entirely. Consequently, none of the functional, type, or schema requirements are satisfied.
- `T015` (rejected 1x): The provided `src/data/process.py` contains utility functions but no `OnlineAccumulator` class or `process_stream` implementation, and the required output files `data/processed/games.parquet` and `data/results/inclusion_counts.json` are absent. Consequently the task’s core functionality and deliverables are not satisfied.
- `T017` (rejected 1x): The repository lacks the required `save_inclusion_metrics` function in `src/data/process.py` (the file ends before any such implementation) and the expected output files `data/results/inclusion_counts.json` and `data/results/inclusion_metrics.json` are absent. Consequently the task’s core logic, file creation, and validation steps are not present.
- `T034` (rejected 1x): No updated `README.md` or `quickstart.md` files are present in the provided evidence; the only artifacts shown relate to statistical analysis specifications, not documentation changes. The required documentation updates are missing.
- `T036` (rejected 1x): No artifact showing that RAM usage was measured and kept below 7 GB is present, nor any code or documentation indicating that data sampling was implemented to achieve this limit. Without performance benchmarks or sampling logic, the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

