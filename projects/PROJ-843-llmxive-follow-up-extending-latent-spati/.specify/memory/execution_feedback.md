# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --phase data_prepare (rc=2); python code/main.py --phase extract_features (rc=2); python code/main.py --phase compute_geometry (rc=2); 1 declared deliverable(s) absent: data/results/sparse_warped_frames.npy

## Failing / missing run-book commands

- python code/main.py --phase data_prepare -> rc=2
    usage: main.py [-h] --phase {prepare,extract,geometry,evaluate,validate,full}
               [--skip-memory]
main.py: error: argument --phase: invalid choice: 'data_prepare' (choose from 'prepare', 'extract', 'geometry', 'evaluate', 'validate', 'full')
- python code/main.py --phase extract_features -> rc=2
    usage: main.py [-h] --phase {prepare,extract,geometry,evaluate,validate,full}
               [--skip-memory]
main.py: error: argument --phase: invalid choice: 'extract_features' (choose from 'prepare', 'extract', 'geometry', 'evaluate', 'validate', 'full')
- python code/main.py --phase compute_geometry -> rc=2
    usage: main.py [-h] --phase {prepare,extract,geometry,evaluate,validate,full}
               [--skip-memory]
main.py: error: argument --phase: invalid choice: 'compute_geometry' (choose from 'prepare', 'extract', 'geometry', 'evaluate', 'validate', 'full')
- python code/main.py --phase evaluate -> rc=2
    ============================================================
Running: /home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/.venv/bin/python /home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/code/eval/download_dense_baseline.py
Description: Phase 6: Download dense baseline frames
============================================================
ERROR: Script failed with return code 2
STDOUT: 
STDERR: /home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/code/eval/download_dense_baseline.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/results/sparse_warped_frames.npy

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `MemoryMonitor` (in `code/utils/memory_monitor.py`) — accessed via method/attribute names this round: `start`

`MemoryMonitor` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/utils/memory_monitor.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `MemoryMonitor` across the codebase must stop raising `AttributeError`/`TypeError`.

`MemoryMonitor.start` call sites (7):
- code/utils/memory_monitor.py: - Can be called with .start()/.stop()
- code/utils/memory_monitor.py: - Can be chained: monitor.start().stop()
- code/utils/memory_monitor.py: tracemalloc.start()
- code/utils/memory_monitor.py: self._thread.start()
- code/utils/memory_monitor.py: return self.start()
- code/utils/memory_monitor.py: monitor.start()
- code/utils/memory_monitor.py: metrics = monitor.start().stop()

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/sparse_warped_frames.npy` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/geometry/run_pipeline.py` — NOT invoked by the run-book
    - `code/geometry/aggregate_warps.py` — NOT invoked by the run-book
    - `code/eval/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sparse_warped_frames.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/results/sparse_warped_frames.npy`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/main.py`, `code/geometry/aggregate_warps.py`, `code/eval/quickstart_validator.py`, `code/eval/metrics.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/results/sparse_warped_frames.npy`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/geometry/run_pipeline.py`, `code/geometry/aggregate_warps.py`, `code/eval/quickstart_validator.py`, `code/eval/metrics.py`.
