# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py --sample-size 100 --timeout 3600 (rc=1); python code/main.py (rc=1); python -m pytest tests/ -v (rc=2); 4 declared deliverable(s) absent: data/artifacts/final_report.json; data/artifacts/permutation_test_results.json; data/artifacts/sensitivity_report.json

## Failing / missing run-book commands

- python code/main.py --sample-size 100 --timeout 3600 -> rc=1
0470/Aluminum_Alloy_Data.csv
2026-10-09 23:20:20,625 - __main__ - ERROR - Pipeline failed with error: Source Unreachable: No valid URLs found.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/main.py", line 200, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/main.py", line 197, in main
    run_pipeline(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/main.py", line 96, in run_pipeline
    run_ingestion_pipeline(args.urls, args.output, args.stats)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 403, in run_pipeline
    valid_urls = verify_source_urls(urls)
                 ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 217, in verify_source_urls
    raise ValueError("Source Unreachable: No valid URLs found.")
ValueError: Source Unreachable: No valid URLs found.

- python code/main.py -> rc=1
0470/Aluminum_Alloy_Data.csv
2026-10-09 23:20:22,896 - __main__ - ERROR - Pipeline failed with error: Source Unreachable: No valid URLs found.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/main.py", line 200, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/main.py", line 197, in main
    run_pipeline(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/main.py", line 96, in run_pipeline
    run_ingestion_pipeline(args.urls, args.output, args.stats)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 403, in run_pipeline
    valid_urls = verify_source_urls(urls)
                 ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/data/ingestion.py", line 217, in verify_source_urls
    raise ValueError("Source Unreachable: No valid URLs found.")
ValueError: Source Unreachable: No valid URLs found.

- python -m pytest tests/ -v -> rc=2
m marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

tests/integration/test_memory_profile.py:239
  /home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/tests/integration/test_memory_profile.py:239: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/analysis/test_reporting.py
ERROR tests/contract/test_ingestion_schema.py
ERROR tests/integration/test_rf_pipeline.py
ERROR tests/unit/test_accumulate_streaming_stats.py
ERROR tests/unit/test_collinearity.py
ERROR tests/unit/test_download.py
ERROR tests/unit/test_ingestion_stats.py
ERROR tests/unit/test_ingestion_streaming.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 2 warnings, 8 errors in 1.53s =========================



## Declared deliverables still missing

- data/artifacts/final_report.json
- data/artifacts/permutation_test_results.json
- data/artifacts/sensitivity_report.json
- data/artifacts/timeout_status.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/final_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/reporting.py` — NOT invoked by the run-book
    - `code/modeling/rf_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/final_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/permutation_test_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/permutation_test_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/timeout_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/artifacts/timeout_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
