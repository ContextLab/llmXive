# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python src/main.py --step acquire; python src/main.py --step pilot; python src/main.py --step generate; 2 declared deliverable(s) absent: data/pilot/tuned_threshold.json; data/validation/integrity_error_report.json

## Failing / missing run-book commands

- python src/main.py --step acquire -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/src/main.py': [Errno 2] No such file or directory
- python src/main.py --step pilot -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/src/main.py': [Errno 2] No such file or directory
- python src/main.py --step generate -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/src/main.py': [Errno 2] No such file or directory
- python src/main.py --step parse -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/src/main.py': [Errno 2] No such file or directory
- python src/main.py --step classify -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/src/main.py': [Errno 2] No such file or directory
- python src/main.py --step stats -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/src/main.py': [Errno 2] No such file or directory
- python src/main.py --step full --sample-size 5 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1072-llmxive-follow-up-extending-blind-spots/src/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/pilot/tuned_threshold.json
- data/validation/integrity_error_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/pilot/tuned_threshold.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_generate_cot.py` — NOT invoked by the run-book
    - `code/03_parse_and_classify.py` — NOT invoked by the run-book
    - `code/tune_threshold.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/pilot/tuned_threshold.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/integrity_error_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_download_and_filter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/integrity_error_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
