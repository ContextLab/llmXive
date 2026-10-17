# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py --stage ingestion (rc=1); python -m pytest code/tests/ -v (rc=2); 4 declared deliverable(s) absent: data/processed/alignment_angles.csv; data/processed/galaxy_properties.csv; data/processed/halo_shapes.csv

## Failing / missing run-book commands

- python code/main.py --stage ingestion -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-107-quantifying-the-effects-of-dark-matter-h/code/main.py", line 182, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-107-quantifying-the-effects-of-dark-matter-h/code/main.py", line 178, in main
    success = stage_map[args.stage](config)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-107-quantifying-the-effects-of-dark-matter-h/code/main.py", line 35, in run_ingestion_stage
    log_pipeline_start(logger, "T011", "Ingestion")
TypeError: log_pipeline_start() takes from 0 to 1 positional arguments but 3 were given

- python -m pytest code/tests/ -v -> rc=2
.__dict__)
code/tests/test_stats.py:14: in <module>
    from code.analysis.stats import (
E   ImportError: cannot import name 'kruskal_wallis_test' from 'code.analysis.stats' (/home/runner/work/llmXive/llmXive/projects/PROJ-107-quantifying-the-effects-of-dark-matter-h/code/analysis/stats.py)
=============================== warnings summary ===============================
code/tests/test_pipeline_runner.py:230
  /home/runner/work/llmXive/llmXive/projects/PROJ-107-quantifying-the-effects-of-dark-matter-h/code/tests/test_pipeline_runner.py:230: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR code/tests/test_alignment_report.py
ERROR code/tests/test_pipeline.py
ERROR code/tests/test_stats.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
=================== 1 skipped, 1 warning, 3 errors in 1.10s ====================



## Declared deliverables still missing

- data/processed/alignment_angles.csv
- data/processed/galaxy_properties.csv
- data/processed/halo_shapes.csv
- data/processed/statistical_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/alignment_angles.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/generate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/integrate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/metadata_utils.py` — NOT invoked by the run-book
    - `code/processing/alignment.py` — NOT invoked by the run-book
    - `code/tests/test_alignment_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alignment_angles.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/galaxy_properties.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/generate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_statistical_results.py` — NOT invoked by the run-book
    - `code/analysis/run_statistical_analysis.py` — NOT invoked by the run-book
    - `code/ingestion/galaxy_loader.py` — NOT invoked by the run-book
    - `code/ingestion/tng_loader.py` — NOT invoked by the run-book
    - `code/processing/alignment.py` — NOT invoked by the run-book
    - `code/tests/test_alignment_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/galaxy_properties.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/halo_shapes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/generate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_statistical_results.py` — NOT invoked by the run-book
    - `code/analysis/integrate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/metadata_utils.py` — NOT invoked by the run-book
    - `code/analysis/run_statistical_analysis.py` — NOT invoked by the run-book
    - `code/processing/alignment.py` — NOT invoked by the run-book
    - `code/processing/pipeline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/halo_shapes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/cross_dataset_comparison.py` — NOT invoked by the run-book
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_statistical_results.py` — NOT invoked by the run-book
    - `code/analysis/integrate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/log_hypothesis_rejections.py` — NOT invoked by the run-book
    - `code/analysis/metadata_utils.py` — NOT invoked by the run-book
    - `code/analysis/run_statistical_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
