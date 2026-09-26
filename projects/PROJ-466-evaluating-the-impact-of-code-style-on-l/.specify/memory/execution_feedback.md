# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 6 declared deliverable(s) absent: data/processed/bias_flag.json; data/processed/metrics_all.csv; data/processed/metrics_valid.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    2026-09-26 04:10:47,715 - matplotlib.font_manager - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: Non-scalable fonts are not supported
2026-09-26 04:10:47,873 - matplotlib.font_manager - INFO - generated new fontManager
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l/code/main.py", line 14, in <module>
    from analysis.reporter import run_reporter_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l/code/analysis/reporter.py", line 12, in <module>
    import seaborn as sns
ModuleNotFoundError: No module named 'seaborn'

## Declared deliverables still missing

- data/processed/bias_flag.json
- data/processed/metrics_all.csv
- data/processed/metrics_valid.csv
- data/processed/samples_all.csv
- data/processed/samples_valid.csv
- data/processed/sensitivity_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/bias_flag.json` is declared but was NOT written. Scripts referencing it:
    - `code/generation/pipeline.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bias_flag.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_all.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/generation/directories.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_all.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_valid.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/generation/directories.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_valid.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/samples_all.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/generation/tester.py` — NOT invoked by the run-book
    - `code/generation/directories.py` — NOT invoked by the run-book
    - `code/generation/pipeline.py` — NOT invoked by the run-book
    - `code/generation/generator.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/samples_all.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/samples_valid.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/generation/tester.py` — NOT invoked by the run-book
    - `code/generation/directories.py` — NOT invoked by the run-book
    - `code/generation/pipeline.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/samples_valid.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
