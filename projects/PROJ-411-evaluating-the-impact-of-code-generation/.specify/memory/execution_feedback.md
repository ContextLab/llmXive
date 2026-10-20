# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python code/classify_provenance.py  --input data/raw/prs-v2-sample.parquet  --output data/processed/classified_prs.csv; python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv; python code/outlier_filter.py --iqr 1.5; 1 command(s) failed: python code/download_data.py (rc=1)

## Failing / missing run-book commands

- python code/download_data.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/download_data.py", line 200, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/download_data.py", line 144, in main
    REQUIRED_FIELDS = load_schema_required_fields(SCHEMA_PATH)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/download_data.py", line 55, in load_schema_required_fields
    with open(schema_path, "r", encoding="utf-8") as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/specs/001-evaluating-the-impact-of-code-generation/contracts/raw_prs.schema.yaml'

- python code/classify_provenance.py  --input data/raw/prs-v2-sample.parquet  --output data/processed/classified_prs.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/classify_provenance.py': [Errno 2] No such file or directory

- python code/compute_metrics.py  --input data/processed/classified_prs.csv  --output data/processed/processed_prs.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-411-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-411-evaluating-the-impact-of-code-generation/code/compute_metrics.py': [Errno 2] No such file or directory

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

