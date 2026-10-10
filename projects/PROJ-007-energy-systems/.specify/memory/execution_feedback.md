# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/tests/unit/test_main.py (rc=1); python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python -c "from src.data.ingest import download_datasets; download_datasets()" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/data/ingest.py", line 16, in <module>
    from src.utils.logging import get_logger
ImportError: cannot import name 'get_logger' from 'src.utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/utils/logging.py)

- python code/tests/unit/test_main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/code/tests/unit/test_main.py", line 4, in <module>
    from src.main import run_pipeline, load_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/main.py", line 25, in <module>
    from src.utils.logging import get_logger, set_seed
ImportError: cannot import name 'get_logger' from 'src.utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/utils/logging.py)

- python -m pytest tests/ -> rc=2
t module '/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/tests/unit/test_report_generation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_report_generation.py:17: in <module>
    from src.reporting.generate_final_report import (
src/reporting/generate_final_report.py:28: in <module>
    from src.models.output import load_analysis_result
E   ModuleNotFoundError: No module named 'src.models.output'
=========================== short test summary info ============================
ERROR tests/integration/test_ingestion.py
ERROR tests/integration/test_pipeline.py
ERROR tests/unit/test_balance.py
ERROR tests/unit/test_ingest.py
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_psm.py
ERROR tests/unit/test_report_generation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 2.09s ===============================


