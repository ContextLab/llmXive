# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/download.py (rc=-1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1); 3 declared deliverable(s) absent: data/processed/exclusion_log.json; data/processed/markov_state.json; data/processed/standardized.csv

## Failing / missing run-book commands

- python code/download.py -> rc=-1
:41,502 - ERROR - Data fetch failed for 42278: Failed to fetch OpenML dataset 42278: https://www.openml.org/api/v1/xml/data/42278 returned code 111: Unknown dataset
2026-10-10 08:17:41,503 - INFO - Processing dataset: 42279
2026-10-10 08:17:41,503 - INFO - Starting [get] request for the URL https://www.openml.org/api/v1/xml/data/42279
2026-10-10 08:17:42,184 - INFO - 0.6805692s taken for [get] request for the URL https://www.openml.org/api/v1/xml/data/42279
2026-10-10 08:17:43,370 - INFO - Redirecting http://data.openml.org/datasets/0004/42279/dataset_42279.pq -> https://data.openml.org:443/datasets/0004/42279/dataset_42279.pq
2026-10-10 08:17:43,887 - WARNING - Could not download file from https://data.openml.org/datasets/0004/42279/dataset_42279.pq: Object at 'https://data.openml.org/datasets/0004/42279/dataset_42279.pq' does not exist.
2026-10-10 08:17:43,887 - INFO - Starting [get] request for the URL https://openml.org/data/v1/download/21799788/BLCA-Part1.arff
2026-10-10 08:17:53,830 - INFO - 9.9429319s taken for [get] request for the URL https://openml.org/data/v1/download/21799788/BLCA-Part1.arff
2026-10-10 08:18:44,480 - INFO - pickle write BLCA-Part1


[TIMEOUT after 120s]
- python code/preprocess.py -> rc=1

INFO:openml.config:No config file found at /home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/.runtime-home/.config/openml/config, using default configuration.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 425, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 416, in main
    success = run_preprocessing_pipeline()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 302, in run_preprocessing_pipeline
    dataset_ids = read_dataset_ids()
                  ^^^^^^^^^^^^^^^^^^
TypeError: read_dataset_ids() missing 1 required positional argument: 'ids_file_path'

- python code/analysis.py -> rc=1
Starting analysis pipeline...
Standardized data not found at data/processed/standardized.csv. Run preprocessing first.

ERROR:root:File not found: data/processed/standardized.csv
ERROR:__main__:Standardized data not found at data/processed/standardized.csv. Run preprocessing first.


## Declared deliverables still missing

- data/processed/exclusion_log.json
- data/processed/markov_state.json
- data/processed/standardized.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/download.py` — IS a run-book command
    - `code/filter_datasets.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/run_preprocessing.py` — NOT invoked by the run-book
    - `code/update_readme.py` — NOT invoked by the run-book
    - `code/update_readme_exclusions.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/markov_state.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_standardized_output.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/run_t017b.py` — NOT invoked by the run-book
    - `code/save_markov_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/markov_state.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/standardized.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/generate_standardized_output.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/run_t017.py` — NOT invoked by the run-book
    - `code/verify_standardized.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/standardized.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
