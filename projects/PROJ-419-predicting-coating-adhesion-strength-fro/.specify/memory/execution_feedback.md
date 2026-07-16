# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1)

## Failing / missing run-book commands

- python code/main.py -> rc=1
    2026-07-16 12:06:59,241 - __main__ - INFO - Pipeline execution started.
2026-07-16 12:06:59,241 - __main__ - INFO - Starting Coating Adhesion Pipeline...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-419-predicting-coating-adhesion-strength-fro/code/main.py", line 263, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-419-predicting-coating-adhesion-strength-fro/code/main.py", line 259, in main
    exit_code = run_pipeline()
                ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-419-predicting-coating-adhesion-strength-fro/code/main.py", line 139, in run_pipeline
    if check_halt_signal():
       ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-419-predicting-coating-adhesion-strength-fro/code/main.py", line 50, in check_halt_signal
    return check_halt_signal(STATE_DIR)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: check_halt_signal() takes 0 positional arguments but 1 was given

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `check_halt_signal` — defined in `code/utils.py`; called 2 way(s):

- code/main.py: return check_halt_signal(STATE_DIR)
- code/main.py: if check_halt_signal():

Make `check_halt_signal` in `code/utils.py` accept ALL of the above.
