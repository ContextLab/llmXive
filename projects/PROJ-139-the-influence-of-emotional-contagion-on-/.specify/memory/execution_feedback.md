# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/analysis/run_pipeline.py`
  - script usage: `download.py [-h] --source SOURCE`
  - argparse error: `download.py: error: the following arguments are required: --source`
- run-book command: `python -m pytest code/tests/ -v`
  - argparse error: `__main__.py: error: unrecognized arguments: --random-seed=42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/data/download.py --source askScience --source fdr (rc=1); python code/analysis/run_pipeline.py (rc=2); python -m pytest code/tests/ -v (rc=4); 9 declared deliverable(s) absent: data/processed/all_threads_classified.csv; data/processed/collinearity_diagnostics.json; data/processed/external_validation_correlation.csv

## Failing / missing run-book commands

- python code/data/download.py --source askScience --source fdr -> rc=1
0-12 00:27:17,820 - WARNING - Internet Archive fallback is not fully implemented for Reddit data.
2026-10-12 00:27:17,821 - ERROR - CRITICAL FAILURE: Could not retrieve any data for subreddit 'askScience' from Pushshift, Reddit API, or Internet Archive. The pipeline cannot proceed without real data. Please check network connectivity, API credentials, or source availability.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/data/download.py", line 271, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/data/download.py", line 262, in main
    download_data(subreddit, output_file)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/data/download.py", line 197, in download_data
    raise RuntimeError(error_msg)
RuntimeError: CRITICAL FAILURE: Could not retrieve any data for subreddit 'askScience' from Pushshift, Reddit API, or Internet Archive. The pipeline cannot proceed without real data. Please check network connectivity, API credentials, or source availability.

- python code/analysis/run_pipeline.py -> rc=2

2026-10-12 00:27:18,856 - INFO - Directories ensured.
2026-10-12 00:27:18,856 - INFO - --- Starting Stage: Data Download ---
usage: download.py [-h] --source SOURCE
download.py: error: the following arguments are required: --source
2026-10-12 00:27:18,857 - INFO - --- Starting Stage: Data Extraction ---
usage: run_pipeline.py [-h] --input INPUT --output OUTPUT --exclusions
                       EXCLUSIONS
run_pipeline.py: error: the following arguments are required: --input, --output, --exclusions

- python -m pytest code/tests/ -v -> rc=4

ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --random-seed=42
  inifile: /home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/pytest.ini
  rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-



## Declared deliverables still missing

- data/processed/all_threads_classified.csv
- data/processed/collinearity_diagnostics.json
- data/processed/external_validation_correlation.csv
- data/processed/ground_truth_stats.json
- data/processed/sensitivity_analysis.csv
- data/processed/thread_metrics.csv
- data/processed/threads_with_seeds.csv
- data/processed/vader_validation_report.json
- data/results/sample_run.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/all_threads_classified.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/analysis/update_analysis_summary.py` — NOT invoked by the run-book
    - `code/data/sampling.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/all_threads_classified.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/collinearity_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_collinearity_heatmap.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/collinearity_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/external_validation_correlation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/generate_report.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_modeling_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/external_validation_correlation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ground_truth_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/validate_ground_truth_coverage.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/tests/test_validate_ground_truth_coverage.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ground_truth_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/analysis/validate_sensitivity_grid.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_final_validation.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_modeling.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/thread_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/data/sampling.py` — NOT invoked by the run-book
    - `code/tests/test_analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/tests/test_final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/thread_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threads_with_seeds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/annotate_corpus.py` — NOT invoked by the run-book
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_metrics.py` — NOT invoked by the run-book
    - `code/tests/test_metrics_data_flow.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threads_with_seeds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vader_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/sentiment_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vader_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sample_run.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/run_pipeline.py` — IS a run-book command
    - `code/tests/test_sample_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sample_run.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
