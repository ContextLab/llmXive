# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/data_ingestion.py --check-only (rc=1); python code/data_ingestion.py --output data/processed/merged_clean.parquet (rc=1); python code/preprocessing.py --input data/processed/merged_clean.parquet --output data/processed/diversity_metrics.parquet (rc=1); 10 declared deliverable(s) absent: data/interim/adjusted_pvals.csv; data/interior/estimated_loss.json; data/interior/median_depth.json

## Failing / missing run-book commands

- python code/data_ingestion.py --check-only -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/data_ingestion.py", line 15, in <module>
    from config import get_output_path, ensure_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/config.py", line 49, in <module>
    raise RuntimeError(
RuntimeError: Missing required environment variable(s): AGP_STUDY_ID, DATA_URL. Please define them in a .env file at the repository root.

- python code/data_ingestion.py --output data/processed/merged_clean.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/data_ingestion.py", line 15, in <module>
    from config import get_output_path, ensure_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/config.py", line 49, in <module>
    raise RuntimeError(
RuntimeError: Missing required environment variable(s): AGP_STUDY_ID, DATA_URL. Please define them in a .env file at the repository root.

- python code/preprocessing.py --input data/processed/merged_clean.parquet --output data/processed/diversity_metrics.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/preprocessing.py", line 9, in <module>
    import biom
ModuleNotFoundError: No module named 'biom'

- python code/analysis.py --input data/processed/diversity_metrics.parquet --output data/results/associations.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/analysis.py", line 7, in <module>
    from skbio.stats.distance import permanova
ModuleNotFoundError: No module named 'skbio'

- python code/visualization.py --input data/results/associations.csv --output docs/figures/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/visualization.py", line 10, in <module>
    from config import get_output_path, ensure_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/config.py", line 49, in <module>
    raise RuntimeError(
RuntimeError: Missing required environment variable(s): AGP_STUDY_ID, DATA_URL. Please define them in a .env file at the repository root.

- python code/report.py --input data/results/associations.csv --output docs/report.md -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/report.py", line 9, in <module>
    from config import get_output_path, ensure_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-215-investigating-the-relationship-between-g/code/config.py", line 49, in <module>
    raise RuntimeError(
RuntimeError: Missing required environment variable(s): AGP_STUDY_ID, DATA_URL. Please define them in a .env file at the repository root.


## Declared deliverables still missing

- data/interim/adjusted_pvals.csv
- data/interior/estimated_loss.json
- data/interior/median_depth.json
- data/processed/alpha_metrics.csv
- data/processed/association_results.csv
- data/processed/bray_curtis.npz
- data/processed/cleaned_dataset.csv
- data/processed/ks_test_results.json
- data/processed/metrics.json
- data/processed/validation_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/adjusted_pvals.csv` is declared but was NOT written. Scripts referencing it:
    - `code/check_covariate_adjustment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/adjusted_pvals.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interior/estimated_loss.json` is declared but was NOT written. Scripts referencing it:
    - `code/preprocessing.py` — IS a run-book command
  Make ONE of these WRITE `data/interior/estimated_loss.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interior/median_depth.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — IS a run-book command
  Make ONE of these WRITE `data/interior/median_depth.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/alpha_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/output_cleaned_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alpha_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/association_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/check_ks_pvalue.py` — NOT invoked by the run-book
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/output_association_results.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/visualization.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/association_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bray_curtis.npz` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/preprocessing.py` — IS a run-book command
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bray_curtis.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/output_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
    - `code/visualization.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ks_test_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/check_ks_pvalue.py` — NOT invoked by the run-book
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/run_visualization_and_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ks_test_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/check_pipeline_runtime.py` — NOT invoked by the run-book
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/output_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/output_validation_results.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/output_validation_results.py` — NOT invoked by the run-book
    - `code/reference_validator.py` — NOT invoked by the run-book
    - `code/run_reference_validator.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
