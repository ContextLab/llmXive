# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/data/download.py --source askScience --source fdr (rc=1); python code/analysis/run_pipeline.py (rc=1); 9 declared deliverable(s) absent: data/processed/all_threads_classified.csv; data/processed/collinearity_diagnostics.json; data/processed/external_validation_correlation.csv

## Failing / missing run-book commands

- python code/data/download.py --source askScience --source fdr -> rc=1
    -08-18 18:17:50,652 - INFO - Attempting Pushshift API...
2026-08-18 18:17:50,842 - INFO - Attempt: https://api.pushshift.io/reddit/search/subreddit/fdr - Status: 404 - Success: False
2026-08-18 18:17:50,843 - INFO - Pushshift failed. Attempting Reddit Official API...
2026-08-18 18:17:50,843 - INFO - Attempt: Reddit API (OAuth) - Status: 0 - Success: False
2026-08-18 18:17:50,843 - INFO - Reddit API failed. Attempting Internet Archive...
2026-08-18 18:17:50,843 - WARNING - Internet Archive fallback is not fully implemented for Reddit data.
2026-08-18 18:17:50,844 - INFO - Attempt: Internet Archive - Status: 0 - Success: False
2026-08-18 18:17:50,844 - ERROR - CRITICAL FAILURE: Could not retrieve any data for subreddit 'fdr' from Pushshift, Reddit API, or Internet Archive. The pipeline cannot proceed without real data. Please check network connectivity, API credentials, or source availability.
2026-08-18 18:17:50,844 - ERROR - Data download failed: CRITICAL FAILURE: Could not retrieve any data for subreddit 'fdr' from Pushshift, Reddit API, or Internet Archive. The pipeline cannot proceed without real data. Please check network connectivity, API credentials, or source availability.
- python code/analysis/run_pipeline.py -> rc=1
    ()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/data/extract.py", line 275, in main
    config = get_config()
             ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/config/settings.py", line 164, in get_config
    _config = load_config_from_env()
              ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/config/settings.py", line 169, in load_config_from_env
    return load_config_from_env()
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/config/settings.py", line 169, in load_config_from_env
    return load_config_from_env()
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/config/settings.py", line 169, in load_config_from_env
    return load_config_from_env()
           ^^^^^^^^^^^^^^^^^^^^^^
  [Previous line repeated 991 more times]
RecursionError: maximum recursion depth exceeded

## Declared deliverables still missing

- data/processed/all_threads_classified.csv
- data/processed/collinearity_diagnostics.json
- data/processed/external_validation_correlation.csv
- data/processed/ground_truth_stats.json
- data/processed/sensitivity_analysis.csv
- data/processed/thread_metrics.csv
- data/processed/threads_with_seeds.csv
- data/processed/vader_validation_report.json
- data/processed/valid_threads.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/all_threads_classified.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/analysis/update_analysis_summary.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/sampling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/all_threads_classified.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/collinearity_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_collinearity_heatmap.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/collinearity_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/external_validation_correlation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/generate_report.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_modeling_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/external_validation_correlation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ground_truth_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validate_ground_truth_coverage.py` — NOT invoked by the run-book
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/tests/test_validate_ground_truth_coverage.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ground_truth_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validate_sensitivity_grid.py` — NOT invoked by the run-book
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_reproducibility.py` — NOT invoked by the run-book
    - `code/tests/test_modeling.py` — NOT invoked by the run-book
    - `code/tests/test_final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/thread_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/data/sampling.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_metrics_decision_quality.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/thread_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threads_with_seeds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/annotate_corpus.py` — NOT invoked by the run-book
    - `code/data/extract.py` — NOT invoked by the run-book
    - `code/tests/test_metrics.py` — NOT invoked by the run-book
    - `code/tests/test_extract.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_metrics_data_flow.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threads_with_seeds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vader_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/sentiment_validation.py` — NOT invoked by the run-book
    - `code/config/settings.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vader_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/valid_threads.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/analysis/validate_ground_truth_coverage.py` — NOT invoked by the run-book
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/data/sentiment.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/annotate_corpus.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/valid_threads.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
