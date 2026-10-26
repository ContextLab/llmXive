# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42`
  - script usage: `main.py [-h] --N-values N_VALUES --noise-levels NOISE_LEVELS`
  - argparse error: `main.py: error: unrecognized arguments: --window-sizes 500,1000,5000`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m pytest -q (rc=1); python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 (rc=2); python -m code.utils.validate --check-all (rc=1)

## Failing / missing run-book commands

- python -m pytest -q -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 148, in _get_module_details
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pytest/__init__.py", line 29, in <module>
    from _pytest.legacypath import TempdirFactory
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/legacypath.py", line 7, in <module>
    import subprocess
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/subprocess.py", line 16, in <module>
    PIPE = _real_subprocess.PIPE
           ^^^^^^^^^^^^^^^^^^^^^
AttributeError: partially initialized module 'subprocess' has no attribute 'PIPE' (most likely due to a circular import)

- python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 -> rc=2

usage: main.py [-h] --N-values N_VALUES --noise-levels NOISE_LEVELS
               [--trials TRIALS] [--seed SEED] [--mode {generate,run-all}]
main.py: error: unrecognized arguments: --window-sizes 500,1000,5000

- python -m code.utils.validate --check-all -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-101-quantifying-the-influence-of-initial-con/bin/python: No module named code.utils.validate

