# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 3 declared deliverable(s) absent: data/processed/baseline_metrics.json; data/processed/cleaned_metrics.json; data/processed/null_fpr_metrics.json

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/baseline_metrics.json
- data/processed/cleaned_metrics.json
- data/processed/null_fpr_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/t036_pvalue_shift_reporting.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t037_ci_width_reporting.py` — NOT invoked by the run-book
    - `code/t034_generate_forest_plot.py` — NOT invoked by the run-book
    - `code/t023_reanalyze_cleaned_variants.py` — NOT invoked by the run-book
    - `code/t035_generate_ci_heatmap.py` — NOT invoked by the run-book
    - `code/t031_bootstrap_variance.py` — NOT invoked by the run-book
    - `code/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/t036_pvalue_shift_reporting.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t037_ci_width_reporting.py` — NOT invoked by the run-book
    - `code/t034_generate_forest_plot.py` — NOT invoked by the run-book
    - `code/t023_reanalyze_cleaned_variants.py` — NOT invoked by the run-book
    - `code/t035_generate_ci_heatmap.py` — NOT invoked by the run-book
    - `code/t031_bootstrap_variance.py` — NOT invoked by the run-book
    - `code/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/null_fpr_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t041_generate_final_report.py` — NOT invoked by the run-book
    - `code/t040_create_comparison_report.py` — NOT invoked by the run-book
    - `code/t032_permutation_null_fpr.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/null_fpr_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
