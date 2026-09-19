# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py --sample-size 100 --timeout 3600 (rc=1); python code/main.py (rc=1); 3 declared deliverable(s) absent: data/artifacts/final_report.json; data/artifacts/permutation_test_results.json; data/artifacts/sensitivity_report.json

## Failing / missing run-book commands

- python code/main.py --sample-size 100 --timeout 3600 -> rc=1
    --urls', 'https://example.com/dataset.csv', '--output', 'data/raw/ingested_data.csv']' returned non-zero exit status 1.

2026-09-19 15:34:48,857 - __main__ - INFO - Starting Ingestion Pipeline
2026-09-19 15:34:48,897 - __main__ - WARNING - URL returned status 404: https://example.com/dataset.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 445, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 442, in main
    run_pipeline(args.urls, args.output, args.stats)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 404, in run_pipeline
    valid_urls = verify_source_urls(urls)
                 ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 140, in verify_source_urls
    raise ValueError("Source Unreachable: No valid URLs found.")
ValueError: Source Unreachable: No valid URLs found.
- python code/main.py -> rc=1
    --urls', 'https://example.com/dataset.csv', '--output', 'data/raw/ingested_data.csv']' returned non-zero exit status 1.

2026-09-19 15:34:51,394 - __main__ - INFO - Starting Ingestion Pipeline
2026-09-19 15:34:51,428 - __main__ - WARNING - URL returned status 404: https://example.com/dataset.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 445, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 442, in main
    run_pipeline(args.urls, args.output, args.stats)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 404, in run_pipeline
    valid_urls = verify_source_urls(urls)
                 ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 140, in verify_source_urls
    raise ValueError("Source Unreachable: No valid URLs found.")
ValueError: Source Unreachable: No valid URLs found.

## Declared deliverables still missing

- data/artifacts/final_report.json
- data/artifacts/permutation_test_results.json
- data/artifacts/sensitivity_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/final_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/modeling/rf_model.py` — NOT invoked by the run-book
    - `code/analysis/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/final_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/permutation_test_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/permutation_test_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
