# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1); 3 declared deliverable(s) absent: data/processed/exclusion_log.json; data/processed/markov_state.json; data/processed/standardized.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/download.py", line 283, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/download.py", line 275, in main
    success = run_download_pipeline()
              ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/download.py", line 178, in run_download_pipeline
    data_dir.mkdir(parents=True, exist_ok=True)
    ^^^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'mkdir'
- python code/preprocess.py -> rc=1
    ERROR:__main__:Preprocessing pipeline failed: unsupported operand type(s) for /: 'str' and 'str'
- python code/analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/analysis.py", line 365, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/analysis.py", line 352, in main
    input_path = str(get_processed_dir() / "standardized.csv")
                     ~~~~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
TypeError: unsupported operand type(s) for /: 'str' and 'str'

## Declared deliverables still missing

- data/processed/exclusion_log.json
- data/processed/markov_state.json
- data/processed/standardized.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/download.py` — IS a run-book command
    - `code/filter_datasets.py` — NOT invoked by the run-book
    - `code/run_preprocessing.py` — NOT invoked by the run-book
    - `code/update_readme_exclusions.py` — NOT invoked by the run-book
    - `code/update_readme.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/markov_state.json` is declared but was NOT written. Scripts referencing it:
    - `code/save_markov_artifacts.py` — NOT invoked by the run-book
    - `code/generate_standardized_output.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/markov_state.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/standardized.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_t017.py` — NOT invoked by the run-book
    - `code/save_markov_artifacts.py` — NOT invoked by the run-book
    - `code/generate_standardized_output.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/standardized.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
