# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/tests/unit/test_main.py (rc=1); python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python -c "from src.data.ingest import download_datasets; download_datasets()" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ImportError: cannot import name 'download_datasets' from 'src.data.ingest' (/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/data/ingest.py)

- python code/tests/unit/test_main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/code/tests/unit/test_main.py", line 4, in <module>
    from src.main import run_pipeline, load_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/main.py", line 28, in <module>
    from src.analysis.psm import iterative_matching
ImportError: cannot import name 'iterative_matching' from 'src.analysis.psm' (/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/analysis/psm.py)

- python -m pytest tests/ -> rc=2
gration/../../src/data/ingest.py)
___________________ ERROR collecting tests/unit/test_psm.py ____________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/tests/unit/test_psm.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_psm.py:4: in <module>
    from src.analysis.psm import estimate_propensity, match_pairs, check_common_support
E   ImportError: cannot import name 'check_common_support' from 'src.analysis.psm' (/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/tests/integration/../../src/analysis/psm.py)
=========================== short test summary info ============================
ERROR tests/integration/test_ingestion.py
ERROR tests/integration/test_pipeline.py
ERROR tests/unit/test_ingest.py
ERROR tests/unit/test_psm.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 1.46s ===============================


## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
