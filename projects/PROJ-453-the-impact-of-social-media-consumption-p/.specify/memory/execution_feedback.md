# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/01_ingest.py (rc=1); python code/02_engineer.py (rc=1); python code/03_model.py (rc=1)

## Failing / missing run-book commands

- python code/01_ingest.py -> rc=1
-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/llmXive/datasets/main/addhealth_wave4.csv

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/01_ingest.py", line 255, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/01_ingest.py", line 226, in main
    raise e
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/01_ingest.py", line 223, in main
    download_data(DATA_URL, raw_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/01_ingest.py", line 107, in download_data
    raise RuntimeError(f"Data fetch failed: {e}") from e
RuntimeError: Data fetch failed: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/llmXive/datasets/main/addhealth_wave4.csv

- python code/02_engineer.py -> rc=1
453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 145, in main
    df = load_all_raw_data()
         ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 56, in load_all_raw_data
    raise FileNotFoundError(f"No cleaned data found in {processed_dir}. Expected *_cleaned.csv")
FileNotFoundError: No cleaned data found in data/processed. Expected *_cleaned.csv

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 179, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 145, in main
    df = load_all_raw_data()
         ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 56, in load_all_raw_data
    raise FileNotFoundError(f"No cleaned data found in {processed_dir}. Expected *_cleaned.csv")
FileNotFoundError: No cleaned data found in data/processed. Expected *_cleaned.csv

- python code/03_model.py -> rc=1
[2026-10-17 21:28:00,586] INFO: Starting Sensitivity Analysis & FDR (T026).
[2026-10-17 21:28:00,586] ERROR: Cleaned data not found at data/processed/participants_cleaned.csv.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/03_model.py", line 296, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/03_model.py", line 247, in main
    raise FileNotFoundError(f"Cleaned data not found: {cleaned_path}")
FileNotFoundError: Cleaned data not found: data/processed/participants_cleaned.csv

- python code/04_visualize.py -> rc=1
[2026-10-17 21:28:01,645] INFO: Starting visualization pipeline (T036-T039).
[2026-10-17 21:28:01,646] ERROR: File not found: Cleaned data not found at data/processed/participants_cleaned.csv


- python -m pytest tests/ -> rc=2
-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_config.py
ERROR tests/unit/test_ingest_errors.py
ERROR tests/unit/test_ruff_config.py
ERROR tests/unit/test_sensitivity_analysis.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 4 errors in 1.20s ========================


