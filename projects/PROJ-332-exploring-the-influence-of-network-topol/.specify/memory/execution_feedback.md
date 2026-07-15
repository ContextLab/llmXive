# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py --run-single --seed 42 (rc=1); python code/main.py --run-grid (rc=1); python code/main.py --sensitivity-only (rc=1)

## Failing / missing run-book commands

- python code/main.py --run-single --seed 42 -> rc=1
    INFO:__main__:Starting thermal conductivity simulation pipeline
INFO:__main__:Loaded 0 existing results
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-332-exploring-the-influence-of-network-topol/code/main.py", line 329, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-332-exploring-the-influence-of-network-topol/code/main.py", line 266, in main
    target_degree=config.target_degree
                  ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'SimulationConfig' object has no attribute 'target_degree'
- python code/main.py --run-grid -> rc=1
    INFO:__main__:Starting thermal conductivity simulation pipeline
INFO:__main__:Loaded 0 existing results
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-332-exploring-the-influence-of-network-topol/code/main.py", line 329, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-332-exploring-the-influence-of-network-topol/code/main.py", line 266, in main
    target_degree=config.target_degree
                  ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'SimulationConfig' object has no attribute 'target_degree'
- python code/main.py --sensitivity-only -> rc=1
    INFO:__main__:Starting thermal conductivity simulation pipeline
INFO:__main__:Loaded 0 existing results
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-332-exploring-the-influence-of-network-topol/code/main.py", line 329, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-332-exploring-the-influence-of-network-topol/code/main.py", line 266, in main
    target_degree=config.target_degree
                  ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'SimulationConfig' object has no attribute 'target_degree'

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `SimulationConfig` (in `code/config.py`) — accessed via method/attribute names this round: `target_degree`

`SimulationConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `SimulationConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`SimulationConfig.target_degree` call sites (0):
