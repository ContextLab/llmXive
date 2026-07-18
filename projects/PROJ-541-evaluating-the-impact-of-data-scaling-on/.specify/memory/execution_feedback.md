# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/main.py --mode simulation (rc=1); python code/main.py --mode real_world (rc=1); python code/main.py --mode simulation --config-id "test-config-1" --iterations 100 (rc=1); 1 declared deliverable(s) absent: figures/error_rate_plot.png

## Failing / missing run-book commands

- python code/main.py --mode simulation -> rc=1
    2026-07-18 22:22:54,878 - main - INFO - Starting Main Pipeline
2026-07-18 22:22:54,878 - main - INFO - Directories ensured.
2026-07-18 22:22:54,878 - main - INFO - Starting Real-World Dataset Ingestion Pipeline (T034b)
2026-07-18 22:22:54,884 - main - INFO - Processing dataset: datasets
2026-07-18 22:22:54,884 - main - WARNING - Failed to process datasets: download_dataset() takes 1 positional argument but 2 were given
2026-07-18 22:22:54,884 - main - INFO - Real-World Ingestion Pipeline finished.
2026-07-18 22:22:54,884 - main - INFO - Starting Real-World Scaling and Testing Pipeline (T038)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 209, in main
    run_full_analysis_pipeline()
TypeError: run_full_analysis_pipeline() missing 1 required positional argument: 'results_df'
- python code/main.py --mode real_world -> rc=1
    2026-07-18 22:22:57,218 - main - INFO - Starting Main Pipeline
2026-07-18 22:22:57,218 - main - INFO - Directories ensured.
2026-07-18 22:22:57,218 - main - INFO - Starting Real-World Dataset Ingestion Pipeline (T034b)
2026-07-18 22:22:57,223 - main - INFO - Processing dataset: datasets
2026-07-18 22:22:57,223 - main - WARNING - Failed to process datasets: download_dataset() takes 1 positional argument but 2 were given
2026-07-18 22:22:57,223 - main - INFO - Real-World Ingestion Pipeline finished.
2026-07-18 22:22:57,223 - main - INFO - Starting Real-World Scaling and Testing Pipeline (T038)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 209, in main
    run_full_analysis_pipeline()
TypeError: run_full_analysis_pipeline() missing 1 required positional argument: 'results_df'
- python code/main.py --mode simulation --config-id "test-config-1" --iterations 100 -> rc=1
    2026-07-18 22:22:59,544 - main - INFO - Starting Main Pipeline
2026-07-18 22:22:59,544 - main - INFO - Directories ensured.
2026-07-18 22:22:59,545 - main - INFO - Starting Real-World Dataset Ingestion Pipeline (T034b)
2026-07-18 22:22:59,550 - main - INFO - Processing dataset: datasets
2026-07-18 22:22:59,550 - main - WARNING - Failed to process datasets: download_dataset() takes 1 positional argument but 2 were given
2026-07-18 22:22:59,550 - main - INFO - Real-World Ingestion Pipeline finished.
2026-07-18 22:22:59,550 - main - INFO - Starting Real-World Scaling and Testing Pipeline (T038)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 209, in main
    run_full_analysis_pipeline()
TypeError: run_full_analysis_pipeline() missing 1 required positional argument: 'results_df'
- python code/main.py --mode visualize -> rc=1
    2026-07-18 22:23:01,935 - main - INFO - Starting Main Pipeline
2026-07-18 22:23:01,936 - main - INFO - Directories ensured.
2026-07-18 22:23:01,936 - main - INFO - Starting Real-World Dataset Ingestion Pipeline (T034b)
2026-07-18 22:23:01,941 - main - INFO - Processing dataset: datasets
2026-07-18 22:23:01,941 - main - WARNING - Failed to process datasets: download_dataset() takes 1 positional argument but 2 were given
2026-07-18 22:23:01,941 - main - INFO - Real-World Ingestion Pipeline finished.
2026-07-18 22:23:01,941 - main - INFO - Starting Real-World Scaling and Testing Pipeline (T038)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 209, in main
    run_full_analysis_pipeline()
TypeError: run_full_analysis_pipeline() missing 1 required positional argument: 'results_df'
- python code/main.py --mode analyze -> rc=1
    2026-07-18 22:23:04,276 - main - INFO - Starting Main Pipeline
2026-07-18 22:23:04,276 - main - INFO - Directories ensured.
2026-07-18 22:23:04,277 - main - INFO - Starting Real-World Dataset Ingestion Pipeline (T034b)
2026-07-18 22:23:04,282 - main - INFO - Processing dataset: datasets
2026-07-18 22:23:04,282 - main - WARNING - Failed to process datasets: download_dataset() takes 1 positional argument but 2 were given
2026-07-18 22:23:04,282 - main - INFO - Real-World Ingestion Pipeline finished.
2026-07-18 22:23:04,282 - main - INFO - Starting Real-World Scaling and Testing Pipeline (T038)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 209, in main
    run_full_analysis_pipeline()
TypeError: run_full_analysis_pipeline() missing 1 required positional argument: 'results_df'
- python code/main.py --mode verify-checksums -> rc=1
    2026-07-18 22:23:06,652 - main - INFO - Starting Main Pipeline
2026-07-18 22:23:06,653 - main - INFO - Directories ensured.
2026-07-18 22:23:06,653 - main - INFO - Starting Real-World Dataset Ingestion Pipeline (T034b)
2026-07-18 22:23:06,658 - main - INFO - Processing dataset: datasets
2026-07-18 22:23:06,658 - main - WARNING - Failed to process datasets: download_dataset() takes 1 positional argument but 2 were given
2026-07-18 22:23:06,658 - main - INFO - Real-World Ingestion Pipeline finished.
2026-07-18 22:23:06,658 - main - INFO - Starting Real-World Scaling and Testing Pipeline (T038)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 209, in main
    run_full_analysis_pipeline()
TypeError: run_full_analysis_pipeline() missing 1 required positional argument: 'results_df'

## Declared deliverables still missing

- figures/error_rate_plot.png

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `run_full_analysis_pipeline` — defined in `code/analysis/metrics.py`; called 1 way(s):

- code/main.py: run_full_analysis_pipeline()

Make `run_full_analysis_pipeline` in `code/analysis/metrics.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `figures/error_rate_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/visualization/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/error_rate_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
