# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python src/main.py --task ingest --dataset openneuro-fslr64k; python src/main.py --task preprocess --subject 001; python src/main.py --task align --subject 001; 3 declared deliverable(s) absent: data/accuracy_blocks.csv; data/aligned_data.csv; data/interim_lagged_mmns.csv

## Failing / missing run-book commands

- python src/main.py --task ingest --dataset openneuro-fslr64k -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory
- python src/main.py --task preprocess --subject 001 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory
- python src/main.py --task align --subject 001 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory
- python src/main.py --task model --all -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory
- python src/main.py --task robustness --windows "140-240,160-260" -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/accuracy_blocks.csv
- data/aligned_data.csv
- data/interim_lagged_mmns.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/accuracy_blocks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_alignment.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t026_finalization.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t023_behavioral_binning.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t025_cleaning.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t024_lagged_alignment.py` — NOT invoked by the run-book
    - `code/src/data/clean.py` — NOT invoked by the run-book
    - `code/src/data/align.py` — NOT invoked by the run-book
    - `code/src/data/finalize.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/accuracy_blocks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/aligned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/contract/test_schemas.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t026_finalization.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t031_permutation_test.py` — NOT invoked by the run-book
    - `code/src/data/finalize.py` — NOT invoked by the run-book
    - `code/src/analysis/model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aligned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim_lagged_mmns.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_alignment.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t026_finalization.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t025_cleaning.py` — NOT invoked by the run-book
    - `code/src/data/clean.py` — NOT invoked by the run-book
    - `code/src/data/align.py` — NOT invoked by the run-book
    - `code/src/data/finalize.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim_lagged_mmns.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
