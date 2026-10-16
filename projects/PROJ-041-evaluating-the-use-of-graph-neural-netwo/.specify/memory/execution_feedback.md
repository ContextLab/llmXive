# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest code/tests/test_graph_construction.py -v (rc=1); 1 declared deliverable(s) absent: data/raw/ctu13_scenario1.csv

## Failing / missing run-book commands

- python -m pytest code/tests/test_graph_construction.py -v -> rc=1
e-packages/pytest_memprof.py:57: ValueError
=============================== warnings summary ===============================
code/tests/test_graph_construction.py::test_memory_limit_exceeded
code/tests/test_graph_construction.py::test_seed_reproducibility
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-041-evaluating-the-use-of-graph-neural-netwo/lib/python3.11/site-packages/_pytest/runner.py:262: PluggyTeardownRaisedWarning: A plugin raised an exception during an old-style hookwrapper teardown.
  Plugin: memprof, Hook: pytest_runtest_call
  ValueError: not enough values to unpack (expected 5, got 4)
  For more information see https://pluggy.readthedocs.io/en/stable/api_reference.html#pluggy.PluggyTeardownRaisedWarning
    lambda: ihook(item=item, **kwds), when=when, reraise=reraise

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED code/tests/test_graph_construction.py::test_memory_limit_exceeded - Va...
FAILED code/tests/test_graph_construction.py::test_seed_reproducibility - Val...
======================== 2 failed, 2 warnings in 1.29s =========================



## Declared deliverables still missing

- data/raw/ctu13_scenario1.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/ctu13_scenario1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/download_ctu13.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ctu13_scenario1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
