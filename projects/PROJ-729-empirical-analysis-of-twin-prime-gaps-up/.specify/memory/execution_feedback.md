# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/analyze_local.py; python code/verify_citations.py; python code/report.py; 2 command(s) failed: python code/analyze_gaps.py (rc=-1); python -m pytest tests/ (rc=-1); 2 declared deliverable(s) absent: data/figures/qq_plot.png; data/results/stats.json

## Failing / missing run-book commands

- python code/analyze_gaps.py -> rc=-1

2026-10-23 09:32:27 - analyze_gaps - INFO - Loaded 3424506 normalized gap values.

[TIMEOUT after 120s]
- python code/analyze_local.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/analyze_local.py': [Errno 2] No such file or directory

- python code/verify_citations.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/verify_citations.py': [Errno 2] No such file or directory

- python code/report.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/report.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=-1
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up
configfile: pyproject.toml
collected 24 items

tests/integration/test_analysis.py 

[TIMEOUT after 120s]

## Declared deliverables still missing

- data/figures/qq_plot.png
- data/results/stats.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/figures/qq_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_gaps.py` — IS a run-book command
  Make ONE of these WRITE `data/figures/qq_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_gaps.py` — IS a run-book command
  Make ONE of these WRITE `data/results/stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
