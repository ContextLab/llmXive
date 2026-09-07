# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory structure or any of the required subfolders (e.g., `code/`, `data/raw`, `data/processed/graphs`, `data/intermediate`, etc.) were presented as evidence, so we cannot confirm that the specified project hierarchy was actually created. The implementer must provide a listing or screenshot showing the full directory tree with all required folders.
- `T001b` (rejected 1x): The required file `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/requirements.txt` does not exist, so the specified dependencies are not placed at the correct location despite a correctly formatted `code/requirements.txt` elsewhere. The task remains unfinished until the file is created at the mandated path with the listed packages.
- `T011a#1` (rejected 1x): The `download_locomo.py` script exists and contains the required logic, but the expected output file `data/raw/locomo.jsonl` is missing, so the task’s primary deliverable was not produced. The implementer must run the script (or otherwise generate) to create the JSONL file with the required columns.
- `T070` (rejected 1x): The task requires `code/runner.py` to verify the existence of `data/intermediate/graphs_raw.json` before execution, but the provided file content is truncated and shows no such validation logic (e.g., an `os.path.exists` check or a `FileNotFoundError` guard) near the entry point. Additionally, the required dependency file `data/intermediate/graphs_raw.json` is explicitly missing from the disk, meaning the runner cannot function as intended even if the check were added.
- `T019a` (rejected 1x): The provided `code/run_lazy.py` is only partially shown and ends abruptly, indicating an incomplete implementation, and the required output file `data/processed/lazy_results.csv` does not exist on disk. Both the runner script and the expected results CSV are missing or incomplete, so the task is not genuinely fulfilled.
- `T024a` (rejected 1x): The repository lacks the required output file `data/processed/stats_clean.json`, and the provided `code/stats.py` does not contain an implementation of `run_ttest_clean()` (the snippet shows other functions but no such function). Both the artifact and the core function are missing, so the task is not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

