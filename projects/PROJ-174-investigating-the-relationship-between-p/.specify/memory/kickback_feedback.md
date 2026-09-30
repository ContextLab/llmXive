# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002b` (rejected 1x): No `code/` directory containing a Python 3.11 virtual environment (e.g., `venv/` or `env/`) or any evidence of dependency installation (such as a `requirements.txt`, `pyproject.toml`, or installed package list) was provided. The required artifact is missing, so the task is not satisfied.
- `T005` (rejected 1x): The provided `code/logging_config.py` is truncated and does not show a complete `LoggingContext` implementation; the required `add_exclusion` and `write_report` methods are missing. Consequently, there is no evidence that calling `LoggingContext.add_exclusion` actually appends rows to `results/quality_report.csv`. The CSV file exists but contains only the header, with no demonstration that the class writes entries. Implement the full `LoggingContext` with the two methods and include a test/assertion that verifies rows are added to the CSV.
- `T013` (rejected 1x): The provided `load_data.py` is truncated (e.g., `col_map = config.ge` is incomplete) and does not contain logic to write the normalized DataFrame to a CSV with the required columns. Moreover, the required `config.yaml` file is missing, so the script cannot be configured as specified. The task’s core requirement—ingesting raw files per configuration and producing a uniform CSV—is therefore not satisfied.
- `T016a` (rejected 1x): The `code/analysis/correlations.py` file is truncated and does not contain a complete implementation (e.g., no function that writes `results/correlations.csv`). Moreover, the required output file `results/correlations.csv` is missing entirely. The task’s output schema is therefore not produced.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

