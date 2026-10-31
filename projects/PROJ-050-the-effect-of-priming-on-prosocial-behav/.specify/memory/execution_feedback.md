# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/00_check_dataset.py   # prints missing fields, exits if title missing`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/03_validate.py; python code/04_analyze.py; 5 command(s) failed: python -m pipeline.run (rc=1); python code/00_check_dataset.py   # prints missing fields, exits if title missing (rc=1); python code/01_ingest.py (rc=1); 1 declared deliverable(s) absent: data/processed/anonymized.csv

## Failing / missing run-book commands

- python -m pipeline.run -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/bin/python: Error while finding module specification for 'pipeline.run' (ModuleNotFoundError: No module named 'pipeline')

- python code/00_check_dataset.py   # prints missing fields, exits if title missing -> rc=1
-prosocial-behav/lib/python3.11/site-packages/datasets/load.py", line 2587, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/lib/python3.11/site-packages/datasets/load.py", line 2259, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/lib/python3.11/site-packages/datasets/load.py", line 1904, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/lib/python3.11/site-packages/datasets/load.py", line 1850, in dataset_module_factory
    raise DatasetNotFoundError(
datasets.exceptions.DatasetNotFoundError: Dataset 'pushshift/reddit' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/pushshift/reddit to ask for access.

- python code/01_ingest.py -> rc=1
2026-10-31 07:07:39 - ingest_feasibility - INFO - === Starting T015b: Feasibility Check for FR-002c ===
2026-10-31 07:07:39 - ingest_feasibility - ERROR - Feasibility check failed: get_logger() missing 1 required positional argument: 'name'


- python code/02_score.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/02_score.py", line 261, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/02_score.py", line 235, in main
    log_abort_condition(f"Input file not found: {input_path}")
TypeError: log_abort_condition() missing 2 required positional arguments: 'reason' and 'condition_name'

- python code/03_validate.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/03_validate.py': [Errno 2] No such file or directory

- python code/04_analyze.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/04_analyze.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
ers, paths
E   ImportError: cannot import name 'paths' from 'code.create_data_folders' (/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/create_data_folders.py)
______________ ERROR collecting tests/unit/test_power_analysis.py ______________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/tests/unit/test_power_analysis.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_power_analysis.py:18: in <module>
    import code._00_power_analysis as power_module
E   ModuleNotFoundError: No module named 'code._00_power_analysis'
=========================== short test summary info ============================
ERROR tests/unit/test_create_data_folders.py
ERROR tests/unit/test_power_analysis.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.90s ===============================



## Declared deliverables still missing

- data/processed/anonymized.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/anonymized.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest.py` — IS a run-book command
    - `code/02_score.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/anonymized.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
