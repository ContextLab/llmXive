# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/cochrane_base_synthetic.csv, data/results/estimation_results.csv, data/results/reml_failures.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/cochrane_base_synthetic.csv, data/results/estimation_results.csv, data/results/reml_failures.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python code/scripts/fetch_cochrane.py (rc=1); python -m pytest tests/unit/ (rc=1); 3 declared deliverable(s) absent: data/raw/cochrane_base.csv; data/results/aggregated_metrics.csv; data/results/stability_analysis.json

## Failing / missing run-book commands

- python code/scripts/fetch_cochrane.py -> rc=1
============================================================
FETCHING COCHRANE DATA
============================================================
Attempting to fetch real data from Zenodo DOI 10.5281/zenodo.10286623 ...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/scripts/fetch_cochrane.py", line 208, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/scripts/fetch_cochrane.py", line 202, in main
    fetch_real_data()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/scripts/fetch_cochrane.py", line 186, in fetch_real_data
    raise FileNotFoundError(
FileNotFoundError: REAL_DATA_FETCH_FAILED: no usable file on Zenodo record 10.5281/zenodo.10286623 (last error: None)

- python -m pytest tests/unit/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/raw/cochrane_base.csv
- data/results/aggregated_metrics.csv
- data/results/stability_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/cochrane_base.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config_loader.py` — NOT invoked by the run-book
    - `code/fetch_cochrane_data.py` — NOT invoked by the run-book
    - `code/generate_synthetic_base.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/scripts/adapt_parameters.py` — NOT invoked by the run-book
    - `code/scripts/fetch_cochrane.py` — IS a run-book command
    - `code/scripts/generate_synthetic_base.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/cochrane_base.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/aggregated_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_metrics.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/aggregated_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/stability_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/run_stability_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stability_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
