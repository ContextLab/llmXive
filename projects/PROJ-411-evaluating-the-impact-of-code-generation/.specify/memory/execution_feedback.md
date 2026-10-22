# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/prs-v2-sample.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/prs-v2-sample.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 run-book script(s) missing (plan/impl path mismatch): python code/outlier_filter.py --iqr 1.5; python code/statistical_analysis.py  --input data/processed/filtered_prs.csv  --results data/results/stats_summary.csv; python code/validation.py  --input data/processed/filtered_prs.csv  --report data/results/validation_report.md; 3 command(s) failed: python code/download_data.py (rc=1); python code/classify_provenance.py  --input data/raw/prs-v2-sample.parquet  --output data/processed/classified_prs.csv (rc=1); python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv (rc=1); 1 declared deliverable(s) absent: data/processed/processed_prs.csv

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
Schema required fields: ['pr_id', 'repo_name', 'created_at', 'merged_at', 'additions', 'deletions', 'comment_count', 'commit_message']
2026-10-22 23:17:07,976 INFO __main__: Schema total fields (including optional): 12
2026-10-22 23:17:07,977 INFO __main__: Downloading primary dataset from HF repo loubnabnl/prs-v2-sample
2026-10-22 23:17:07,977 INFO __main__: Listing files for repo loubnabnl/prs-v2-sample
2026-10-22 23:17:08,135 INFO __main__: Downloading data/train-00000-of-00001-a3494cf8c0712e34.parquet from loubnabnl/prs-v2-sample
2026-10-22 23:17:08,705 INFO __main__: Combined parquet written to /home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/data/raw/prs-v2-sample.parquet
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/download_data.py", line 239, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/download_data.py", line 188, in main
    raise RuntimeError(
RuntimeError: Primary dataset is missing mandatory fields required for scope: ['comment_count', 'merged_at']

- python code/classify_provenance.py  --input data/raw/prs-v2-sample.parquet  --output data/processed/classified_prs.csv -> rc=1
 precedence collapses to commit-message tier.
2026-10-22 23:17:09,362 INFO __main__: Applying provenance classification...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/classify_provenance.py", line 139, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/classify_provenance.py", line 116, in main
    repo_llm_counts = df[df["provenance_label"] == "LLM-generated"].groupby("repo_name").size()
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py", line 9183, in groupby
    return DataFrameGroupBy(
           ^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/groupby/groupby.py", line 1329, in __init__
    grouper, exclusions, obj = get_grouper(
                               ^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/groupby/grouper.py", line 1043, in get_grouper
    raise KeyError(gpr)
KeyError: 'repo_name'

- python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/compute_metrics.py", line 160, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/compute_metrics.py", line 112, in main
    raise FileNotFoundError(f"Input file {input_path} not found. Ensure classify_provenance.py ran successfully.")
FileNotFoundError: Input file data/processed/classified_prs.csv not found. Ensure classify_provenance.py ran successfully.

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
