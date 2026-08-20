# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --config code/config.py (rc=1); python code/main.py --step extraction (rc=1); python code/main.py --step analysis (rc=1); 9 declared deliverable(s) absent: data/artifacts/regression_plot.png; data/processed/aligned_dataset.csv; data/processed/aligned_reader_response.csv

## Failing / missing run-book commands

- python code/main.py --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/main.py", line 11, in <module>
    from data_loader import fetch_gutenberg_stories, fetch_external_moral_dataset, prepare_sensitivity_thresholds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/data_loader.py", line 10, in <module>
    def fetch_gutenberg_stories(output_dir: str, authors: List[str] = None) -> List[str]:
                                                          ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
- python code/main.py --step extraction -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/main.py", line 11, in <module>
    from data_loader import fetch_gutenberg_stories, fetch_external_moral_dataset, prepare_sensitivity_thresholds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/data_loader.py", line 10, in <module>
    def fetch_gutenberg_stories(output_dir: str, authors: List[str] = None) -> List[str]:
                                                          ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
- python code/main.py --step analysis -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/main.py", line 11, in <module>
    from data_loader import fetch_gutenberg_stories, fetch_external_moral_dataset, prepare_sensitivity_thresholds
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/data_loader.py", line 10, in <module>
    def fetch_gutenberg_stories(output_dir: str, authors: List[str] = None) -> List[str]:
                                                          ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
- python -m pytest tests/contract/ -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/.venv/bin/python: No module named pytest

## Declared deliverables still missing

- data/artifacts/regression_plot.png
- data/processed/aligned_dataset.csv
- data/processed/aligned_reader_response.csv
- data/processed/analysis_results.json
- data/processed/matching_results.json
- data/processed/perspective_features.json
- data/processed/sensitivity_report.json
- data/processed/thresholds.json
- data/raw/gold_standard_annotations.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/regression_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/regression_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aligned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/aligned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aligned_reader_response.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/aligned_reader_response.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/matching_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/matching.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/matching_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/perspective_features.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/perspective_features.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/thresholds.json` is declared but was NOT written. Scripts referencing it:
    - `code/matching.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/thresholds.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/gold_standard_annotations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/gold_standard_annotations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
