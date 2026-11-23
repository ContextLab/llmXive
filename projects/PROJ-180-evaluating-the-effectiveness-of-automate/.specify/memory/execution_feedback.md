# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/02_human_annotation.py; python code/03_alignment.py; python code/04_metrics.py; 1 command(s) failed: python code/01_data_acquisition.py (rc=1); 1 declared deliverable(s) absent: data/processed/heuristic_candidates.json

## Failing / missing run-book commands

- python code/01_data_acquisition.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/01_data_acquisition.py", line 11, in <module>
    from utils.config import get_config, get_github_token, get_data_raw_dir, get_data_processed_dir
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/utils/config.py", line 5, in <module>
    from dotenv import load_dotenv
ModuleNotFoundError: No module named 'dotenv'
- python code/02_human_annotation.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/02_human_annotation.py': [Errno 2] No such file or directory
- python code/03_alignment.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/03_alignment.py': [Errno 2] No such file or directory
- python code/04_metrics.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/04_metrics.py': [Errno 2] No such file or directory
- python code/05_regression.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-180-evaluating-the-effectiveness-of-automate/code/05_regression.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/heuristic_candidates.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/heuristic_candidates.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_human_baseline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/heuristic_candidates.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
