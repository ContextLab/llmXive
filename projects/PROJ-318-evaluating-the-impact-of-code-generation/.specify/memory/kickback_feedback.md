# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The required `data/raw/frozen_repo_list.json` (and its copy `repo_list.json`) are absent, and the provided `code/utils/repo_fetcher.py` is incomplete/truncated and does not demonstrably implement the fetching, sorting, validation, and writing logic required to produce a JSON array of exactly 20 entries. The task’s core output artifact is missing.
- `T033` (rejected 1x): The required `data/processed/results.json` and the generated `data/processed/results_with_coverage.json` are both missing, so the script cannot be run and no coverage scores are produced. Additionally, the provided `code/analyze.py` snippet does not show a command‑line interface handling `--step=coverage`, and without the input file the coverage calculation cannot be verified. The implementer must ensure the input JSON exists, run the script to produce the output file, and confirm each record contains a `coverage_score` field.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

