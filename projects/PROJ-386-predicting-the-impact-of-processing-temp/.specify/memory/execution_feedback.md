# Execution failures — fix these before the analysis can run

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python code/main.py --sample-size 100 --timeout 3600`
- `python code/main.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py --sample-size 100 --timeout 3600 (rc=1); python code/main.py (rc=1); 1 declared deliverable(s) absent: data/artifacts/final_report.json

## Failing / missing run-book commands

- python code/main.py --sample-size 100 --timeout 3600 -> rc=1
    2026-09-19 15:19:54,416 - INFO - Verifying runner environment...
2026-09-19 15:19:54,416 - INFO - No GPU detected. Running on CPU.
2026-09-19 15:19:54,416 - INFO - Detected CPU count: 4
2026-09-19 15:19:54,416 - INFO - Total RAM: 15.61 GB
2026-09-19 15:19:54,416 - INFO - Runner environment verified.
2026-09-19 15:19:54,416 - INFO - Starting pipeline execution...
2026-09-19 15:19:54,417 - ERROR - No dataset URLs found in configuration. Cannot proceed with ingestion.
2026-09-19 15:19:54,417 - WARNING - Skipping Data Ingestion due to missing URLs.
2026-09-19 15:19:54,417 - INFO - Executing Data Preprocessing: /home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/.venv/bin/python code/data/preprocessing.py
2026-09-19 15:19:58,842 - ERROR - Data preprocessing failed with code 1
2026-09-19 15:19:58,842 - ERROR - Pipeline failed with unexpected error: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/.venv/bin/python', 'code/data/preprocessing.py']' returned non-zero exit status 1.

2026-09-19 15:19:57,487 - __main__ - ERROR - Pipeline failed: 'processed_data'
- python code/main.py -> rc=1
    2026-09-19 15:20:00,669 - INFO - Verifying runner environment...
2026-09-19 15:20:00,669 - INFO - No GPU detected. Running on CPU.
2026-09-19 15:20:00,670 - INFO - Detected CPU count: 4
2026-09-19 15:20:00,670 - INFO - Total RAM: 15.61 GB
2026-09-19 15:20:00,670 - INFO - Runner environment verified.
2026-09-19 15:20:00,670 - INFO - Starting pipeline execution...
2026-09-19 15:20:00,670 - ERROR - No dataset URLs found in configuration. Cannot proceed with ingestion.
2026-09-19 15:20:00,670 - WARNING - Skipping Data Ingestion due to missing URLs.
2026-09-19 15:20:00,670 - INFO - Executing Data Preprocessing: /home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/.venv/bin/python code/data/preprocessing.py
2026-09-19 15:20:03,743 - ERROR - Data preprocessing failed with code 1
2026-09-19 15:20:03,743 - ERROR - Pipeline failed with unexpected error: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/.venv/bin/python', 'code/data/preprocessing.py']' returned non-zero exit status 1.

2026-09-19 15:20:03,251 - __main__ - ERROR - Pipeline failed: 'processed_data'

## Declared deliverables still missing

- data/artifacts/final_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/final_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/modeling/rf_model.py` — NOT invoked by the run-book
    - `code/analysis/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/final_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
