# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data_loader.py --prepare (rc=1); python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5 (rc=1); python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5 (rc=1)

## Failing / missing run-book commands

- python code/data_loader.py --prepare -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/data_loader.py", line 244, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/data_loader.py", line 213, in main
    parser = argparse.ArgumentParser(description="Prepare data for llmXive pipeline.")
             ^^^^^^^^
NameError: name 'argparse' is not defined
- python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5 -> rc=1
    2026-07-19 09:23:55,707 - logging_config - INFO - Logging initialized

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 216, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 181, in main
    check_data_integrity()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 41, in check_data_integrity
    os.path.join(config.data_dir, 'processed', 'injected_datasets.json'),
                 ^^^^^^^^^^^^^^^
AttributeError: 'PipelineConfig' object has no attribute 'data_dir'
- python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5 -> rc=1
    2026-07-19 09:24:01,543 - logging_config - INFO - Logging initialized

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 216, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 181, in main
    check_data_integrity()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 41, in check_data_integrity
    os.path.join(config.data_dir, 'processed', 'injected_datasets.json'),
                 ^^^^^^^^^^^^^^^
AttributeError: 'PipelineConfig' object has no attribute 'data_dir'
- python code/run_pipeline.py --variant unique_baseline --budgets 20 50 100 --seeds 5 -> rc=1
    2026-07-19 09:24:07,329 - logging_config - INFO - Logging initialized

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 216, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 181, in main
    check_data_integrity()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-873-llmxive-follow-up-extending-active-learn/code/run_pipeline.py", line 41, in check_data_integrity
    os.path.join(config.data_dir, 'processed', 'injected_datasets.json'),
                 ^^^^^^^^^^^^^^^
AttributeError: 'PipelineConfig' object has no attribute 'data_dir'

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `PipelineConfig` (in `code/config.py`) — accessed via method/attribute names this round: `data_dir`

`PipelineConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `PipelineConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`PipelineConfig.data_dir` call sites (0):
