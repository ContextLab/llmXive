# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --phase data_prepare (rc=1); python code/main.py --phase extract_features (rc=1); python code/main.py --phase compute_geometry (rc=1); 1 declared deliverable(s) absent: data/raw/dense_baseline_frames.npy

## Failing / missing run-book commands

- python code/main.py --phase data_prepare -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 32, in <module>
    from config import (
ImportError: cannot import name 'get_raw_dir' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/config.py)
- python code/main.py --phase extract_features -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 32, in <module>
    from config import (
ImportError: cannot import name 'get_raw_dir' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/config.py)
- python code/main.py --phase compute_geometry -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 32, in <module>
    from config import (
ImportError: cannot import name 'get_raw_dir' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/config.py)
- python code/main.py --phase evaluate -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 32, in <module>
    from config import (
ImportError: cannot import name 'get_raw_dir' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/config.py)

## Declared deliverables still missing

- data/raw/dense_baseline_frames.npy

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_directories` — defined in `code/config.py`; called 16 way(s):

- code/config.py: - ensure_directories()
- code/config.py: - ensure_directories(Path(...))
- code/config.py: - ensure_directories([Path(...), Path(...), ...])
- code/config.py: - ensure_directories(Path(...), Path(...), ...)
- code/main.py: ensure_directories()
- code/validate_quickstart.py: ensure_directories()
- code/geometry/run_pipeline.py: ensure_directories()
- code/geometry/aggregate_warps.py: ensure_directories([results_dir])
- code/data/schemas.py: ensure_directories()
- code/eval/download_dense_baseline.py: ensure_directories(raw_dir)
- code/eval/quickstart_validator.py: ensure_directories()
- code/eval/run_dense_baseline.py: ensure_directories()
- code/eval/anova.py: ensure_directories()
- code/eval/sensitivity.py: ensure_directories(output_path.parent)
- code/eval/sensitivity.py: ensure_directories(get_results_dir())
- code/eval/metrics.py: ensure_directories([raw_dir, results_dir])

Make `ensure_directories` in `code/config.py` accept ALL of the above.

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

`MemoryMonitor.start` call sites (1):
- code/utils/memory_monitor.py: self._thread.start()

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/dense_baseline_frames.npy` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/eval/download_dense_baseline.py` — NOT invoked by the run-book
    - `code/eval/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/run_dense_baseline.py` — NOT invoked by the run-book
    - `code/eval/sensitivity.py` — NOT invoked by the run-book
    - `code/eval/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dense_baseline_frames.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/raw/dense_baseline_frames.npy`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/main.py`, `code/eval/quickstart_validator.py`, `code/eval/sensitivity.py`, `code/eval/metrics.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/dense_baseline_frames.npy`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/eval/download_dense_baseline.py`, `code/eval/quickstart_validator.py`, `code/eval/run_dense_baseline.py`, `code/eval/sensitivity.py`, `code/eval/metrics.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/results/sparse_warped_frames.npy`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/main.py`, `code/geometry/aggregate_warps.py`, `code/eval/quickstart_validator.py`, `code/eval/sensitivity.py`, `code/eval/metrics.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/results/sparse_warped_frames.npy`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/geometry/run_pipeline.py`, `code/geometry/aggregate_warps.py`, `code/eval/quickstart_validator.py`, `code/eval/sensitivity.py`, `code/eval/metrics.py`.
