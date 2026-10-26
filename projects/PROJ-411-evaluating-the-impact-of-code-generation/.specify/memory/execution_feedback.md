# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python code/outlier_filter.py  --input data/processed/processed_prs.csv  --iqr 1.5   # produces filtered_prs_iqr1.5.csv, plus 1.0/2.0 and relaxed variants; python code/statistical_analysis.py  --input data/processed/filtered_prs_iqr1.5.csv  --results data/results/stats_summary.csv; python code/validation.py  --aux-dataset prs-eth/AGBD  --output data/results/validation_report.md; 3 command(s) failed: python code/download_data.py --repo-list code/repo_list.txt --output data/raw/ (rc=-1); python code/classify_provenance.py  --input data/raw/combined_prs.json  --output data/processed/classified_prs.csv (rc=1); python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv (rc=1); 1 declared deliverable(s) absent: data/processed/processed_prs.csv

## Failing / missing run-book commands

- python code/download_data.py --repo-list code/repo_list.txt --output data/raw/ -> rc=-1

2026-10-26 17:14:03,026 INFO __main__: Schema required fields: ['pr_id', 'repo_name', 'created_at', 'merged_at', 'additions', 'deletions', 'comment_count', 'commit_message', 'first_comment_timestamp']
2026-10-26 17:14:03,042 WARNING __main__: Rate limit exhausted. Sleeping for 2678s until reset.

[TIMEOUT after 120s]
- python code/classify_provenance.py  --input data/raw/combined_prs.json  --output data/processed/classified_prs.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/classify_provenance.py", line 139, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/classify_provenance.py", line 92, in main
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/raw/combined_prs.json

- python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/compute_metrics.py", line 160, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/compute_metrics.py", line 112, in main
    raise FileNotFoundError(f"Input file {input_path} not found. Ensure classify_provenance.py ran successfully.")
FileNotFoundError: Input file data/processed/classified_prs.csv not found. Ensure classify_provenance.py ran successfully.

- python code/outlier_filter.py  --input data/processed/processed_prs.csv  --iqr 1.5   # produces filtered_prs_iqr1.5.csv, plus 1.0/2.0 and relaxed variants -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/outlier_filter.py': [Errno 2] No such file or directory

- python code/statistical_analysis.py  --input data/processed/filtered_prs_iqr1.5.csv  --results data/results/stats_summary.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/statistical_analysis.py': [Errno 2] No such file or directory

- python code/validation.py  --aux-dataset prs-eth/AGBD  --output data/results/validation_report.md -> rc=2

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
