# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest -m contract (rc=5)

## Failing / missing run-book commands

- python -m pytest -m contract -> rc=5
==
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: dash-4.5.0
collected 7 items / 7 deselected / 0 selected

=============================== warnings summary ===============================
tests/test_ingest_check.py:19
  /home/runner/work/llmXive/llmXive/projects/PROJ-323-predicting-glass-transition-temperature-/tests/test_ingest_check.py:19: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(300)

tests/test_memory_usage.py:20
  /home/runner/work/llmXive/llmXive/projects/PROJ-323-predicting-glass-transition-temperature-/tests/test_memory_usage.py:20: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(300)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
====================== 7 deselected, 2 warnings in 0.95s =======================


## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
