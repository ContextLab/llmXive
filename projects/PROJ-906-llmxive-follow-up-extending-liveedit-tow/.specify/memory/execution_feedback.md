# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py --stage data_prep --dataset davis --stratify (rc=1); python code/main.py --stage flow_compute --method farneback (rc=1); python code/main.py --stage inference --model baseline (rc=1); 3 declared deliverable(s) absent: data/metrics/analysis_results.json; data/metrics/baseline_results.json; data/metrics/flow_results.json

## Failing / missing run-book commands

- python code/main.py --stage data_prep --dataset davis --stratify -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 15, in <module>
    from utils.logger import get_logger, setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/__init__.py", line 6, in <module>
    from .checkpoint import CheckpointManager
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/checkpoint.py", line 15, in <module>
    logger = get_logger("checkpoint")
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 98, in get_logger
    setup_logging()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 52, in setup_logging
    ensure_directories(log_dir)
TypeError: ensure_directories() takes 0 positional arguments but 1 was given
- python code/main.py --stage flow_compute --method farneback -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 15, in <module>
    from utils.logger import get_logger, setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/__init__.py", line 6, in <module>
    from .checkpoint import CheckpointManager
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/checkpoint.py", line 15, in <module>
    logger = get_logger("checkpoint")
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 98, in get_logger
    setup_logging()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 52, in setup_logging
    ensure_directories(log_dir)
TypeError: ensure_directories() takes 0 positional arguments but 1 was given
- python code/main.py --stage inference --model baseline -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 15, in <module>
    from utils.logger import get_logger, setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/__init__.py", line 6, in <module>
    from .checkpoint import CheckpointManager
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/checkpoint.py", line 15, in <module>
    logger = get_logger("checkpoint")
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 98, in get_logger
    setup_logging()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 52, in setup_logging
    ensure_directories(log_dir)
TypeError: ensure_directories() takes 0 positional arguments but 1 was given
- python code/main.py --stage inference --model flow_coherence -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 15, in <module>
    from utils.logger import get_logger, setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/__init__.py", line 6, in <module>
    from .checkpoint import CheckpointManager
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/checkpoint.py", line 15, in <module>
    logger = get_logger("checkpoint")
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 98, in get_logger
    setup_logging()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 52, in setup_logging
    ensure_directories(log_dir)
TypeError: ensure_directories() takes 0 positional arguments but 1 was given
- python code/main.py --stage analysis --method ks_test --sweep 0.01,0.05,0.1 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 15, in <module>
    from utils.logger import get_logger, setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/__init__.py", line 6, in <module>
    from .checkpoint import CheckpointManager
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/checkpoint.py", line 15, in <module>
    logger = get_logger("checkpoint")
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 98, in get_logger
    setup_logging()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/utils/logger.py", line 52, in setup_logging
    ensure_directories(log_dir)
TypeError: ensure_directories() takes 0 positional arguments but 1 was given

## Declared deliverables still missing

- data/metrics/analysis_results.json
- data/metrics/baseline_results.json
- data/metrics/flow_results.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_directories` — defined in `code/config.py`; called 10 way(s):

- code/main.py: ensure_directories(output_dir)
- code/config.py: ensure_directories()
- code/utils/logger.py: ensure_directories(log_dir)
- code/data/flow.py: ensure_directories([output_dir])
- code/data/flow.py: ensure_directories([os.path.dirname(output_path)])
- code/data/processor.py: ensure_directories()
- code/data/downloader.py: ensure_directories([output_dir])
- code/analysis/reporter.py: ensure_directories([output_path])
- code/analysis/reporter.py: ensure_directories([BASELINE_RESULTS_PATH, FLOW_RESULTS_PATH, ANALYSIS_RESULTS_PATH])
- code/analysis/stats.py: ensure_directories()

Make `ensure_directories` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metrics/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/reporter.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/baseline_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/reporter.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/baseline_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/flow_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data/flow.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/flow_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
