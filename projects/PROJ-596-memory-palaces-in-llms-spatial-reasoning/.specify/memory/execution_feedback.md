# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/trainer.py --seed 0 --dataset babi_task3 --variant spatial; 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python src/trainer.py --seed 0 --dataset babi_task3 --variant spatial -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/src/trainer.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/data/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
