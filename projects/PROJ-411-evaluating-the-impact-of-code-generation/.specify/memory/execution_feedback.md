# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/classified_prs.csv: header only, ZERO data rows — the analysis produced no rows
- results/group_source_contingency.csv: header only, ZERO data rows — the analysis produced no rows

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/classified_prs.csv: header only, ZERO data rows — the analysis produced no rows; results/group_source_contingency.csv: header only, ZERO data rows — the analysis produced no rows; 5 run-book script(s) missing (plan/impl path mismatch): python code/outlier_filter.py --iqr 1.5; python code/statistical_analysis.py  --input data/processed/filtered_prs.csv  --results data/results/stats_summary.csv; python code/validation.py  --input data/processed/filtered_prs.csv  --report data/results/validation_report.md; 1 command(s) failed: python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv (rc=1); 1 declared deliverable(s) absent: data/processed/processed_prs.csv

## Failing / missing run-book commands

- python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv -> rc=1

2026-10-22 01:24:59,027 INFO __main__: Loading classified PRs from data/processed/classified_prs.csv
2026-10-22 01:24:59,030 ERROR __main__: Input dataset is empty. Cannot compute metrics.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/compute_metrics.py", line 160, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/compute_metrics.py", line 122, in main
    raise RuntimeError("Input dataset is empty.")
RuntimeError: Input dataset is empty.

- python code/outlier_filter.py --iqr 1.5 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/outlier_filter.py': [Errno 2] No such file or directory

- python code/statistical_analysis.py  --input data/processed/filtered_prs.csv  --results data/results/stats_summary.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/statistical_analysis.py': [Errno 2] No such file or directory

- python code/validation.py  --input data/processed/filtered_prs.csv  --report data/results/validation_report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/validation.py': [Errno 2] No such file or directory

- python code/sensitivity.py --mode full -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/sensitivity.py': [Errno 2] No such file or directory

- python code/report.py  --stats data/results/stats_summary.csv  --validation data/results/validation_report.md  --output report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/report.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/processed_prs.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/processed_prs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/compute_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/processed_prs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
