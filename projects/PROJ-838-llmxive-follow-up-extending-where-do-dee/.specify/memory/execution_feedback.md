# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/metrics.csv: header only, ZERO data rows — the analysis produced no rows
- every produced artifact is gitignored (data/processed/metrics.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/metrics.csv: header only, ZERO data rows — the analysis produced no rows; every produced artifact is gitignored (data/processed/metrics.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/pipeline.py --config code/config.py (rc=1); python -m pytest tests/unit/ -v (rc=1); python -m pytest tests/integration/ -v (rc=1); 12 declared deliverable(s) absent: data/processed/baseline_report.json; data/processed/comparative_report.json; data/processed/cutoff_depth_validation.json

## Failing / missing run-book commands

- python code/pipeline.py --config code/config.py -> rc=1
^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1643, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1907, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/train_metrics.csv'

- python -m pytest tests/unit/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/.venv/bin/python: No module named pytest

- python -m pytest tests/integration/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/processed/baseline_report.json
- data/processed/comparative_report.json
- data/processed/cutoff_depth_validation.json
- data/processed/f1_max_threshold.json
- data/processed/power_analysis.json
- data/processed/results_report.json
- data/processed/sc_002_result.json
- data/processed/sensitivity_percentile_matrix.json
- data/processed/sensitivity_threshold_matrix.json
- data/processed/test_metrics.csv
- data/processed/threshold_config.json
- data/processed/train_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/comparative_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/comparative_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cutoff_depth_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cutoff_depth_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/f1_max_threshold.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/f1_max_threshold.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
    - `code/run_evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sc_002_result.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sc_002_result.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_percentile_matrix.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_percentile_matrix.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_threshold_matrix.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_threshold_matrix.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
