# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/main.py --task generate --config code/config.py (rc=1); python code/main.py --task generate_control --config code/config.py (rc=1); python code/main.py --task select_validation_sample --config code/config.py (rc=1); 1 declared deliverable(s) absent: data/processed/validity_scores.csv

## Failing / missing run-book commands

- python code/main.py --task generate --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 14, in <module>
    from config import CONFIG
ImportError: cannot import name 'CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/.venv/lib/python3.11/site-packages/config/__init__.py)
- python code/main.py --task generate_control --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 14, in <module>
    from config import CONFIG
ImportError: cannot import name 'CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/.venv/lib/python3.11/site-packages/config/__init__.py)
- python code/main.py --task select_validation_sample --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 14, in <module>
    from config import CONFIG
ImportError: cannot import name 'CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/.venv/lib/python3.11/site-packages/config/__init__.py)
- python code/main.py --task analyze -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 14, in <module>
    from config import CONFIG
ImportError: cannot import name 'CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/.venv/lib/python3.11/site-packages/config/__init__.py)
- python code/main.py --task validate_human -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 14, in <module>
    from config import CONFIG
ImportError: cannot import name 'CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/.venv/lib/python3.11/site-packages/config/__init__.py)
- python code/main.py --task stats -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 14, in <module>
    from config import CONFIG
ImportError: cannot import name 'CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/.venv/lib/python3.11/site-packages/config/__init__.py)
- python code/main.py --task sensitivity-kappa -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 14, in <module>
    from config import CONFIG
ImportError: cannot import name 'CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/.venv/lib/python3.11/site-packages/config/__init__.py)

## Declared deliverables still missing

- data/processed/validity_scores.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/validity_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/validity_justification.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/validation/stratified_sampler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validity_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
