# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/download.py --source askScience --source fdr`
  - script usage: `download.py [-h] [--output OUTPUT]`
  - argparse error: `download.py: error: unrecognized arguments: --source askScience --source fdr`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/data/download.py --source askScience --source fdr (rc=2); python code/analysis/run_pipeline.py (rc=1); 9 declared deliverable(s) absent: data/processed/all_threads_classified.csv; data/processed/collinearity_diagnostics.json; data/processed/external_validation_correlation.csv

## Failing / missing run-book commands

- python code/data/download.py --source askScience --source fdr -> rc=2
    usage: download.py [-h] [--output OUTPUT]
                   [--subreddits SUBREDDITS [SUBREDDITS ...]] [--limit LIMIT]
                   [--reddit-client-id REDDIT_CLIENT_ID]
                   [--reddit-client-secret REDDIT_CLIENT_SECRET]
                   [--reddit-user-agent REDDIT_USER_AGENT]
download.py: error: unrecognized arguments: --source askScience --source fdr
- python code/analysis/run_pipeline.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/analysis/run_pipeline.py", line 14, in <module>
    from data.download import download_data
ModuleNotFoundError: No module named 'data.download'

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
    - `code/analysis/update_analysis_summary.py` — NOT invoked by the run-book
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/data/sampling.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/all_threads_classified.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/collinearity_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/collinearity_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/external_validation_correlation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
    - `code/tests/test_modeling_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/generate_report.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/external_validation_correlation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ground_truth_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ground_truth_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_modeling.py` — NOT invoked by the run-book
    - `code/tests/test_final_validation.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
    - `code/tests/test_reproducibility.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/config/settings.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/thread_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/tests/test_modeling.py` — NOT invoked by the run-book
    - `code/tests/test_final_validation.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
    - `code/tests/test_metrics_decision_quality.py` — NOT invoked by the run-book
    - `code/tests/test_reproducibility.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/thread_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threads_with_seeds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_extract.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
    - `code/tests/test_metrics.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/data/annotate_corpus.py` — NOT invoked by the run-book
    - `code/data/extract.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threads_with_seeds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vader_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/config/settings.py` — NOT invoked by the run-book
    - `code/data/sentiment_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vader_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/valid_threads.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/analysis/run_pipeline.py` — IS a run-book command
    - `code/tests/test_final_validation.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
    - `code/tests/test_reproducibility.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_sentiment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/valid_threads.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
