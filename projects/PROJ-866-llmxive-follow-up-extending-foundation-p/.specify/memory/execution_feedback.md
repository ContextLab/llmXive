# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python src/cli/run_simulation.py --generate --seed [RANDOM_SEED] --count 500; python src/cli/run_simulation.py --execute --mode full; python src/cli/run_simulation.py --execute --mode compressed --depths 1,2,3,4,5,6,7,8,9,10; 1 command(s) failed: python -m pytest tests/ -v (rc=2)

## Failing / missing run-book commands

- python src/cli/run_simulation.py --generate --seed [RANDOM_SEED] --count 500 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --execute --mode full -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --execute --mode compressed --depths 1,2,3,4,5,6,7,8,9,10 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python src/cli/run_simulation.py --analyze --bootstraps [sufficient_resampling_iterations] -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-866-llmxive-follow-up-extending-foundation-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/src/cli/run_simulation.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=2
nit/test_update_state_registry.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_update_state_registry.py:8: in <module>
    from code.utils.update_state_registry import (
E   ImportError: cannot import name 'collect_all_artifact_hashes' from 'code.utils.update_state_registry' (/home/runner/work/llmXive/llmXive/projects/PROJ-866-llmxive-follow-up-extending-foundation-p/code/utils/update_state_registry.py)
=========================== short test summary info ============================
ERROR tests/security/test_network_isolation.py - NameError: name 'List' is no...
ERROR tests/unit/test_finalize_state.py
ERROR tests/unit/test_invalid_exclusion.py
ERROR tests/unit/test_pm4py_integration.py
ERROR tests/unit/test_reproducibility.py
ERROR tests/unit/test_state_manager.py
ERROR tests/unit/test_update_state_registry.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 1.17s ===============================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
