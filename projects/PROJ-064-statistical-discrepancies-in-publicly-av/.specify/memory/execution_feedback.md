# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/discrepancy_calc.py --input data/processed/unified_election_data.parquet --output data/processed/discrepancies.parquet; python code/viz.py --input data/processed/analysis_results.json --output-dir docs/plots; 5 command(s) failed: python code/ingestion.py --source "synthetic" --state "CA" (rc=1); python code/simulation.py --input data/processed/discrepancies.parquet --iterations 10000 --seed 42 (rc=1); python code/analysis.py --input data/processed/null_distributions.json --threshold 0.005 (rc=1)

## Failing / missing run-book commands

- python code/ingestion.py --source "synthetic" --state "CA" -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/ingestion.py", line 13, in <module>
    from error_handling import error_handler_factory, handle_errors, safe_execute, validate_required_fields, validate_input_types, log_function_call
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/error_handling.py", line 10, in <module>
    from .exceptions import (
ImportError: attempted relative import with no known parent package

- python code/discrepancy_calc.py --input data/processed/unified_election_data.parquet --output data/processed/discrepancies.parquet -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/discrepancy_calc.py': [Errno 2] No such file or directory

- python code/simulation.py --input data/processed/discrepancies.parquet --iterations 10000 --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/simulation.py", line 6, in <module>
    from scipy.optimize import OptimizeError
ImportError: cannot import name 'OptimizeError' from 'scipy.optimize' (/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/.venv/lib/python3.11/site-packages/scipy/optimize/__init__.py)

- python code/analysis.py --input data/processed/null_distributions.json --threshold 0.005 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/analysis.py", line 10, in <module>
    import matplotlib.pyplot as plt
ModuleNotFoundError: No module named 'matplotlib'

- python code/viz.py --input data/processed/analysis_results.json --output-dir docs/plots -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/viz.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/.venv/bin/python: No module named pytest

- python -m pytest tests/integration/test_pipeline.py -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-064-statistical-discrepancies-in-publicly-av/code/.venv/bin/python: No module named pytest

