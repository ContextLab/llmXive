# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/preprocess.py (rc=1); python code/analysis.py (rc=1); 2 declared deliverable(s) absent: data/processed/markov_state.json; data/processed/standardized.csv

## Failing / missing run-book commands

- python code/preprocess.py -> rc=1
    asets: OpenML dataset not found: data/raw/# HuggingFace datasets.csv
INFO:__main__:Processing dataset: # Add verified datasets here as they are discovered
ERROR:__main__:Failed to load OpenML dataset # Add verified datasets here as they are discovered: OpenML dataset not found: data/raw/# Add verified datasets here as they are discovered.csv
ERROR:__main__:Failed to process dataset # Add verified datasets here as they are discovered: OpenML dataset not found: data/raw/# Add verified datasets here as they are discovered.csv
INFO:__main__:Processing dataset: # Example: psycholab/time-perception
ERROR:__main__:Failed to load HuggingFace dataset # Example: psycholab/time-perception: Repo id must use alphanumeric chars, '-', '_' or '.'. The name cannot start or end with '-' or '.' and the maximum length is 96: '# Example: psycholab/time-perception'.
ERROR:__main__:Failed to process dataset # Example: psycholab/time-perception: Repo id must use alphanumeric chars, '-', '_' or '.'. The name cannot start or end with '-' or '.' and the maximum length is 96: '# Example: psycholab/time-perception'.
ERROR:__main__:No data processed from any dataset
ERROR:__main__:Preprocessing pipeline failed
- python code/analysis.py -> rc=1
    2026-09-23 03:54:24,736 - INFO - Starting analysis pipeline...
2026-09-23 03:54:24,736 - ERROR - Data loading failed: Standardized data not found at data/processed/standardized.csv. Run preprocessing first.
2026-09-23 03:54:24,736 - INFO - Analysis pipeline completed successfully.
2026-09-23 03:54:24,736 - INFO - Analysis completed successfully
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/analysis.py", line 316, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/analysis.py", line 311, in main
    logger.info(f"Primary result method: {results.get('test_method_used', 'LMM')}")
                                          ^^^^^^^
NameError: name 'results' is not defined

## Declared deliverables still missing

- data/processed/markov_state.json
- data/processed/standardized.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/markov_state.json` is declared but was NOT written. Scripts referencing it:
    - `code/save_markov_artifacts.py` — NOT invoked by the run-book
    - `code/generate_standardized_output.py` — NOT invoked by the run-book
    - `code/run_t017b.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/markov_state.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/standardized.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_t017.py` — NOT invoked by the run-book
    - `code/save_markov_artifacts.py` — NOT invoked by the run-book
    - `code/generate_standardized_output.py` — NOT invoked by the run-book
    - `code/verify_standardized.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/standardized.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
