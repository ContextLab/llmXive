# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely CANNOT be measured on a CPU (it needs a GPU), do NOT fake it — measure a different, genuinely-computable proxy and name it honestly, or report that the metric is unmeasurable here. Never present a simulated number as a measurement.

- code/.venv/lib/python3.11/site-packages/PIL/ImageCms.py: self-declared fabricated metric — “…outputProfile``, but tries to simulate the result that would be     obtained on…”
- code/.venv/lib/python3.11/site-packages/PIL/ImageCms.py: self-declared fabricated metric — “…outputProfile``, but tries to simulate the result that would be     obtained on…”
- code/.venv/lib/python3.11/site-packages/_pytest/subtests.py: self-declared fabricated metric — “…:param kwargs:             Arbitrary values that are also added to the s…”
- code/.venv/lib/python3.11/site-packages/anyio/_backends/_asyncio.py: self-declared fabricated metric — “…_queue = deque(maxlen=100)  # arbitrary value         self.read_event = asy…”
- code/.venv/lib/python3.11/site-packages/attr/_make.py: self-declared fabricated metric — “…yping.Callable]):             Arbitrary number of validators.      .. versio…”
- code/.venv/lib/python3.11/site-packages/attr/_make.py: self-declared fabricated metric — “…yping.Callable]):             Arbitrary number of converters.      .. versio…”
- code/.venv/lib/python3.11/site-packages/attr/validators.py: self-declared fabricated metric — “…yping.Callable]):             Arbitrary number of validators.      Raises:…”
- code/.venv/lib/python3.11/site-packages/click/core.py: self-declared fabricated metric — “…in how it works but supports arbitrary number of                      argum…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 102 fabricated/simulated-result signal(s) — results are not real measurements: code/.venv/lib/python3.11/site-packages/PIL/ImageCms.py: self-declared fabricated metric — “…outputProfile``, but tries to simulate the result that would be     obtained on…”; code/.venv/lib/python3.11/site-packages/PIL/ImageCms.py: self-declared fabricated metric — “…outputProfile``, but tries to simulate the result that would be     obtained on…”; code/.venv/lib/python3.11/site-packages/_pytest/subtests.py: self-declared fabricated metric — “…:param kwargs:             Arbitrary values that are also added to the s…”; 6 command(s) failed: python src/benchmark/run_benchmark.py --config default.yaml (rc=1); python src/benchmark/run_task.py --task-id 3 --add-modality image (rc=1); python src/benchmark/run_benchmark.py --config default.yaml --mode unified (rc=1)

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
