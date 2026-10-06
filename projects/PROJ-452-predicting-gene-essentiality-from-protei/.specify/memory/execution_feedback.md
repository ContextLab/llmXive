# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/data/download_string.py; python code/data/download_deg.py; python code/data/download_depmap.py; 1 command(s) failed: python code/main.py (rc=1)

## Failing / missing run-book commands

- python code/data/download_string.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-452-predicting-gene-essentiality-from-protei/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-452-predicting-gene-essentiality-from-protei/code/data/download_string.py': [Errno 2] No such file or directory
- python code/data/download_deg.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-452-predicting-gene-essentiality-from-protei/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-452-predicting-gene-essentiality-from-protei/code/data/download_deg.py': [Errno 2] No such file or directory
- python code/data/download_depmap.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-452-predicting-gene-essentiality-from-protei/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-452-predicting-gene-essentiality-from-protei/code/data/download_depmap.py': [Errno 2] No such file or directory
- python code/main.py -> rc=1
    2026-10-06 16:26:23 - root - INFO - Setting deterministic random seed to 42 for reproducibility
2026-10-06 16:26:23 - __main__ - INFO - Pipeline initialized with seed 42
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-452-predicting-gene-essentiality-from-protei/code/main.py", line 346, in <module>
    exit(main())
         ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-452-predicting-gene-essentiality-from-protei/code/main.py", line 298, in main
    organisms = get_organisms()
                ^^^^^^^^^^^^^^^
TypeError: get_organisms() missing 1 required positional argument: 'config'

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_organisms` — defined in `code/config.py`; called 4 way(s):

- code/main.py: organisms = get_organisms()
- code/fetch_phylogeny.py: organisms = get_organisms(config)
- code/statistics.py: current_organisms = get_organisms(current_config)
- code/statistics.py: organisms = get_organisms(config)

Make `get_organisms` in `code/config.py` accept ALL of the above.
