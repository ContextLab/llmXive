# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/preprocess.py; python code/analysis.py; python code/visualize.py; 2 command(s) failed: python code/download.py --subjects 2 (rc=-1); python -m pytest code/tests/ (rc=4); 1 declared deliverable(s) absent: data/results/citation_verification.json

## Failing / missing run-book commands

- python code/download.py --subjects 2 -> rc=-1
 0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  1 92.5M    1  968k    0     0  1335k      0  0:01:11 --:--:--  0:01:11 1334k 46 92.5M   46 43.4M    0     0  24.9M      0  0:00:03  0:00:01  0:00:02 24.9M100 92.5M  100 92.5M    0     0  36.3M      0  0:00:02  0:00:02 --:--:-- 36.3M
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  2 98.4M    2 2858k    0     0  3544k      0  0:00:28 --:--:--  0:00:28 3542k 54 98.4M   54 53.8M    0     0  29.6M      0  0:00:03  0:00:01  0:00:02 29.6M100 98.4M  100 98.4M    0     0  38.5M      0  0:00:02  0:00:02 --:--:-- 38.5M
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  1  121M    1 2174k    0     0  2517k      0  0:00:49 --:--:--  0:00:49 2516k 50  121M   50 61.1M    0     0  33.1M      0  0:00:03  0:00:01  0:00:02 33.1M
[TIMEOUT after 120s]
- python code/preprocess.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-250-neural-correlates-of-temporal-prediction/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/code/preprocess.py': [Errno 2] No such file or directory

- python code/analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-250-neural-correlates-of-temporal-prediction/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/code/analysis.py': [Errno 2] No such file or directory

- python code/visualize.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-250-neural-correlates-of-temporal-prediction/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/code/visualize.py': [Errno 2] No such file or directory

- python -m pytest code/tests/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: code/tests/



## Declared deliverables still missing

- data/results/citation_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/citation_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_references.py` — IS a run-book command
  Make ONE of these WRITE `data/results/citation_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
