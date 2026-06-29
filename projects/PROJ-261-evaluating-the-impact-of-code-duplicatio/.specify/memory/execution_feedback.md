# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py (rc=1); python code/data_loader.py # Stage 1: Download data (rc=2); python code/ast_cloner.py # Stage 2: Clone detection (rc=2); 1 declared deliverable(s) absent: data/raw/github-code-sample.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    HF_TOKEN to enable higher rate limits and faster downloads.
2026-06-29 15:08:59,027 - data_loader - ERROR - Download failed: Dataset scripts are no longer supported, but found github-code.py

2026-06-29 15:08:59,171 - __main__ - ERROR - Pipeline failed with exception: data_loader.py failed with return code 1
2026-06-29 15:08:59,171 - memory_monitor - INFO - Memory monitoring stopped. Peak: 0.00 MB
- python code/data_loader.py # Stage 1: Download data -> rc=2
    usage: data_loader.py [-h] [--output OUTPUT] [--max-samples MAX_SAMPLES]
                      [--dataset DATASET] [--config CONFIG] [--streaming]
                      [--log-file LOG_FILE]
data_loader.py: error: unrecognized arguments: # Stage 1: Download data
- python code/ast_cloner.py # Stage 2: Clone detection -> rc=2
    usage: ast_cloner.py [-h] --input INPUT --output OUTPUT [--log-file LOG_FILE]
ast_cloner.py: error: the following arguments are required: --input, --output
- python code/model_metrics.py # Stage 3: Perplexity computation -> rc=2
    usage: model_metrics.py [-h] --input INPUT --output OUTPUT [--model MODEL]
                        [--max-length MAX_LENGTH] [--device DEVICE]
model_metrics.py: error: the following arguments are required: --input, --output
- python code/quickstart_validation.py -> rc=1
    Usage: python quickstart_validation.py <command>
Commands: validate_directory_structure, validate_config_documentation,
          validate_checksum_manifest, validate_quickstart_documentation,
          validate_output_files, validate_quickstart_steps, main

## Declared deliverables still missing

- data/raw/github-code-sample.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `setup_memory_monitoring` — defined in `code/memory_monitor.py`; called 3 way(s):

- code/memory_monitor.py: setup_memory_monitoring(log_dir=log_dir)
- code/memory_monitor.py: setup_memory_monitoring(log_dir="data/logs", logger=logger)
- code/main.py: setup_memory_monitoring()

Make `setup_memory_monitoring` in `code/memory_monitor.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/github-code-sample.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data_loader.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/github-code-sample.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
