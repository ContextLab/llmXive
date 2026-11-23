# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/us1_main.py --step download (rc=1); python code/us1_main.py --step full (rc=1); python -m pytest tests/ (rc=2); 2 declared deliverable(s) absent: data/derived/cli_time_series.parquet; data/derived/passage_data.parquet

## Failing / missing run-book commands

- python code/us1_main.py --step download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati/code/us1_main.py", line 231, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati/code/us1_main.py", line 203, in main
    logger = setup_pipeline_logger("us1_main", config.log_dir)
                                               ^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'log_dir'. Did you mean: 'logs_dir'?

- python code/us1_main.py --step full -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati/code/us1_main.py", line 231, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati/code/us1_main.py", line 203, in main
    logger = setup_pipeline_logger("us1_main", config.log_dir)
                                               ^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'log_dir'. Did you mean: 'logs_dir'?

- python -m pytest tests/ -> rc=2
tests/unit/test_simulation.py ________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati/tests/unit/test_simulation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_simulation.py:11: in <module>
    from simulation import (
E   ImportError: cannot import name '_simplify_text_with_t5' from 'simulation' (/home/runner/work/llmXive/llmXive/projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati/code/simulation.py)
=========================== short test summary info ============================
ERROR tests/integration/test_us1_main.py
ERROR tests/integration/test_us1_pipeline.py
ERROR tests/integration/test_us2_simulation.py
ERROR tests/unit/test_simulation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 1.63s ===============================



## Declared deliverables still missing

- data/derived/cli_time_series.parquet
- data/derived/passage_data.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/cli_time_series.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/us1_main.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/cli_time_series.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/passage_data.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/simulation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/passage_data.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
