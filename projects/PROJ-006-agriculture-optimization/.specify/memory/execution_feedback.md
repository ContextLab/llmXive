# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/cli/validate.py --input data/processed/analysis_dataset.csv --contract contracts/dataset.schema.yaml`
  - script usage: `validate.py [-h] --schema-type {dataset,regression,sensitivity}`
  - argparse error: `validate.py: error: the following arguments are required: --schema-type`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python src/cli/run_pipeline.py --stage ingest (rc=1); python src/cli/run_pipeline.py --stage ingest --use-synthetic (rc=1); python src/cli/run_pipeline.py --stage full (rc=1); 6 declared deliverable(s) absent: data/logs/linkage_validation.json; data/processed/analysis_dataset.csv; data/processed/analysis_dataset_village_aggregated.csv

## Failing / missing run-book commands

- python src/cli/run_pipeline.py --stage ingest -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-006-agriculture-optimization/src/cli/run_pipeline.py", line 8, in <module>
    from src.data.generators.synthetic_generator import SyntheticDataGenerator, main as generate_synthetic_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-006-agriculture-optimization/code/src/data/generators/synthetic_generator.py", line 13, in <module>
    logger = setup_logging("synthetic_generator")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-006-agriculture-optimization/code/src/utils/io_helpers.py", line 25, in setup_logging
    raise ValueError(f"Invalid log level: {level}")
ValueError: Invalid log level: synthetic_generator
- python src/cli/run_pipeline.py --stage ingest --use-synthetic -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-006-agriculture-optimization/src/cli/run_pipeline.py", line 8, in <module>
    from src.data.generators.synthetic_generator import SyntheticDataGenerator, main as generate_synthetic_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-006-agriculture-optimization/code/src/data/generators/synthetic_generator.py", line 13, in <module>
    logger = setup_logging("synthetic_generator")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-006-agriculture-optimization/code/src/utils/io_helpers.py", line 25, in setup_logging
    raise ValueError(f"Invalid log level: {level}")
ValueError: Invalid log level: synthetic_generator
- python src/cli/run_pipeline.py --stage full -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-006-agriculture-optimization/src/cli/run_pipeline.py", line 8, in <module>
    from src.data.generators.synthetic_generator import SyntheticDataGenerator, main as generate_synthetic_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-006-agriculture-optimization/code/src/data/generators/synthetic_generator.py", line 13, in <module>
    logger = setup_logging("synthetic_generator")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-006-agriculture-optimization/code/src/utils/io_helpers.py", line 25, in setup_logging
    raise ValueError(f"Invalid log level: {level}")
ValueError: Invalid log level: synthetic_generator
- python src/cli/validate.py --input data/processed/analysis_dataset.csv --contract contracts/dataset.schema.yaml -> rc=2
    usage: validate.py [-h] --schema-type {dataset,regression,sensitivity}
                   [--no-strict]
                   [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                   file_path
validate.py: error: the following arguments are required: --schema-type

## Declared deliverables still missing

- data/logs/linkage_validation.json
- data/processed/analysis_dataset.csv
- data/processed/analysis_dataset_village_aggregated.csv
- data/processed/regression_results.json
- data/processed/sensitivity_metrics.json
- data/processed/sensitivity_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/linkage_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/processing/spatial_join.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/linkage_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/sensitivity_check.py` — NOT invoked by the run-book
    - `code/src/analysis/run_regression.py` — NOT invoked by the run-book
    - `code/src/data/processing/spatial_join.py` — NOT invoked by the run-book
    - `code/src/data/generators/synthetic_generator.py` — NOT invoked by the run-book
    - `code/src/cli/run_pipeline.py` — NOT invoked by the run-book
    - `code/tests/contract/test_validate_cli.py` — NOT invoked by the run-book
    - `code/tests/integration/test_ingestion.py` — NOT invoked by the run-book
    - `code/scripts/validate_dataset_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_dataset_village_aggregated.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/processing/spatial_join.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_dataset_village_aggregated.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/run_regression.py` — NOT invoked by the run-book
    - `code/src/services/report_generator.py` — NOT invoked by the run-book
    - `code/src/cli/run_pipeline.py` — NOT invoked by the run-book
    - `code/tests/contract/test_validate_cli.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/sensitivity_check.py` — NOT invoked by the run-book
    - `code/src/services/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/sensitivity_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
