# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python -m code.data_loader`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m code.data_loader (rc=1); python code/main.py (rc=1); 1 declared deliverable(s) absent: data/processed/clone_metrics.csv

## Failing / missing run-book commands

- python -m code.data_loader -> rc=1
    ule_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1177, in dataset_module_factory
    raise RuntimeError(f"Dataset scripts are no longer supported, but found {filename}")
RuntimeError: Dataset scripts are no longer supported, but found github-code.py
- python code/main.py -> rc=1
    ule_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1177, in dataset_module_factory
    raise RuntimeError(f"Dataset scripts are no longer supported, but found {filename}")
RuntimeError: Dataset scripts are no longer supported, but found github-code.py

## Declared deliverables still missing

- data/processed/clone_metrics.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `compute_clone_density_batch` — defined in `code/ast_cloner.py`; called 2 way(s):

- code/ast_cloner.py: compute_clone_density_batch(input_path=raw_dir)
- code/main.py: compute_clone_density_batch(input_path=raw_dir)

Make `compute_clone_density_batch` in `code/ast_cloner.py` accept ALL of the above.

### `download_and_save_sample` — defined in `code/data_loader.py`; called 2 way(s):

- code/main.py: raw_csv_path = download_and_save_sample()
- code/data_loader.py: download_and_save_sample()

Make `download_and_save_sample` in `code/data_loader.py` accept ALL of the above.

### `setup_memory_monitoring` — defined in `code/memory_monitor.py`; called 2 way(s):

- code/memory_monitor.py: setup_memory_monitoring()
- code/main.py: setup_memory_monitoring()

Make `setup_memory_monitoring` in `code/memory_monitor.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clone_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/ast_cloner.py` — NOT invoked by the run-book
    - `code/correlation_analysis.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clone_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
