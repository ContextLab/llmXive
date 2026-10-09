# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/load.py --generate-synthetic --seed 42 --n-participants 60 --null-effect`
  - script usage: `load.py [-h] [--null-effect] [--output OUTPUT]`
  - argparse error: `load.py: error: unrecognized arguments: --generate-synthetic --seed 42 --n-participants 60`
- run-book command: `python code/data/load.py --generate-synthetic --seed 42 --n-participants 60`
  - script usage: `load.py [-h] [--null-effect] [--output OUTPUT]`
  - argparse error: `load.py: error: unrecognized arguments: --generate-synthetic --seed 42 --n-participants 60`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/data/load.py --generate-synthetic --seed 42 --n-participants 60 --null-effect (rc=2); python code/data/load.py --generate-synthetic --seed 42 --n-participants 60 (rc=2); python code/main.py --process-stimuli --aggregate-responses (rc=1); 1 declared deliverable(s) absent: data/results/d_score_comparison.png

## Failing / missing run-book commands

- python code/data/load.py --generate-synthetic --seed 42 --n-participants 60 --null-effect -> rc=2

usage: load.py [-h] [--null-effect] [--output OUTPUT]
load.py: error: unrecognized arguments: --generate-synthetic --seed 42 --n-participants 60

- python code/data/load.py --generate-synthetic --seed 42 --n-participants 60 -> rc=2

usage: load.py [-h] [--null-effect] [--output OUTPUT]
load.py: error: unrecognized arguments: --generate-synthetic --seed 42 --n-participants 60

- python code/main.py --process-stimuli --aggregate-responses -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-026-the-influence-of-visual-complexity-on-im/code/main.py", line 23, in <module>
    from stimuli.process import main as run_stimuli_main
ImportError: cannot import name 'main' from 'stimuli.process' (/home/runner/work/llmXive/llmXive/projects/PROJ-026-the-influence-of-visual-complexity-on-im/code/stimuli/process.py)

- python code/main.py --run-analysis -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-026-the-influence-of-visual-complexity-on-im/code/main.py", line 23, in <module>
    from stimuli.process import main as run_stimuli_main
ImportError: cannot import name 'main' from 'stimuli.process' (/home/runner/work/llmXive/llmXive/projects/PROJ-026-the-influence-of-visual-complexity-on-im/code/stimuli/process.py)

- python -m pytest code/tests/ -v -> rc=5
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/projects/PROJ-026-the-influence-of-visual-complexity-on-im/code/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-026-the-influence-of-visual-complexity-on-im/code
configfile: pyproject.toml
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================



## Declared deliverables still missing

- data/results/d_score_comparison.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/d_score_comparison.png` is declared but was NOT written. Scripts referencing it:
    - `code/viz/generate_report.py` — NOT invoked by the run-book
    - `code/viz/plot.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/d_score_comparison.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
