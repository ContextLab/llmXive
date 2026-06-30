# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python src/benchmark/run_benchmark.py --config default.yaml (rc=1); python src/benchmark/run_task.py --task-id 3 --add-modality image (rc=1); python src/benchmark/run_benchmark.py --config default.yaml --mode unified (rc=1)

## Failing / missing run-book commands

- python src/benchmark/run_benchmark.py --config default.yaml -> rc=1
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-573-https-arxiv-org-abs-2604-27351/src/benchmark/run_benchmark.py", line 73, in run_single_task
    runner = TaskRunner(config=config)  # ``TaskRunner`` now tolerates the ``config`` kwarg.
             ^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: TaskRunner.__init__() got an unexpected keyword argument 'config'
- python src/benchmark/run_task.py --task-id 3 --add-modality image -> rc=1
    ", line 155, in main
    task_def = load_task_definition(args.task_id)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-573-https-arxiv-org-abs-2604-27351/src/benchmark/run_task.py", line 66, in load_task_definition
    tasks_list = all_tasks.get("tasks", [])
                 ^^^^^^^^^^^^^
AttributeError: 'list' object has no attribute 'get'
- python src/benchmark/run_benchmark.py --config default.yaml --mode unified -> rc=1
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-573-https-arxiv-org-abs-2604-27351/src/benchmark/run_benchmark.py", line 73, in run_single_task
    runner = TaskRunner(config=config)  # ``TaskRunner`` now tolerates the ``config`` kwarg.
             ^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: TaskRunner.__init__() got an unexpected keyword argument 'config'
- python src/benchmark/run_task.py --task-id 3 --add-modality image -> rc=1
    ", line 155, in main
    task_def = load_task_definition(args.task_id)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-573-https-arxiv-org-abs-2604-27351/src/benchmark/run_task.py", line 66, in load_task_definition
    tasks_list = all_tasks.get("tasks", [])
                 ^^^^^^^^^^^^^
AttributeError: 'list' object has no attribute 'get'
- python src/benchmark/run_benchmark.py --seed 42 -> rc=1
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-573-https-arxiv-org-abs-2604-27351/src/benchmark/run_benchmark.py", line 73, in run_single_task
    runner = TaskRunner(config=config)  # ``TaskRunner`` now tolerates the ``config`` kwarg.
             ^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: TaskRunner.__init__() got an unexpected keyword argument 'config'
- python src/benchmark/run_benchmark.py --seed 123 -> rc=1
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-573-https-arxiv-org-abs-2604-27351/src/benchmark/run_benchmark.py", line 73, in run_single_task
    runner = TaskRunner(config=config)  # ``TaskRunner`` now tolerates the ``config`` kwarg.
             ^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: TaskRunner.__init__() got an unexpected keyword argument 'config'

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `TaskRunner` (in `code/src/tasks/task_runner.py`) — accessed via method/attribute names this round: `__init__`

`TaskRunner` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/src/tasks/task_runner.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `TaskRunner` across the codebase must stop raising `AttributeError`/`TypeError`.

`TaskRunner.__init__` call sites (0):
