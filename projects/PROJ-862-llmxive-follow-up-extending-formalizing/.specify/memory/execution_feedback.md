# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 11 declared deliverable(s) absent: data/processed/baseline_vectors.csv; data/processed/filtered_pairs_for_analysis.csv; data/processed/filtered_pairs_output_validity.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/main.py", line 37, in <module>
    from validity_check import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/validity_check.py", line 10, in <module>
    from bert_score import score
ModuleNotFoundError: No module named 'bert_score'

## Declared deliverables still missing

- data/processed/baseline_vectors.csv
- data/processed/filtered_pairs_for_analysis.csv
- data/processed/filtered_pairs_output_validity.csv
- data/processed/global_trade_off_curve.csv
- data/processed/memory_profile.json
- data/processed/pairing_config.json
- data/processed/perturbed_vectors.csv
- data/processed/sensitivity_report.json
- data/processed/statistical_results.json
- data/processed/trade_off_curve.csv
- data/processed/validity_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_vectors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/validate_vectors.py` — NOT invoked by the run-book
    - `code/verify_baseline_extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_vectors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_pairs_for_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_pairs_for_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_pairs_output_validity.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_pairs_output_validity.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/global_trade_off_curve.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/plot_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/global_trade_off_curve.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/memory_profile.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/memory_monitor.py` — NOT invoked by the run-book
    - `code/inconclusive_report.py` — NOT invoked by the run-book
    - `code/verify_baseline_extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/memory_profile.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pairing_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/verify_baseline_extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pairing_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/perturbed_vectors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/save_perturbed_vectors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/perturbed_vectors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/plot_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trade_off_curve.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/inconclusive_report.py` — NOT invoked by the run-book
    - `code/plot_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trade_off_curve.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validity_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/validity_check.py` — NOT invoked by the run-book
    - `code/inconclusive_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validity_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
