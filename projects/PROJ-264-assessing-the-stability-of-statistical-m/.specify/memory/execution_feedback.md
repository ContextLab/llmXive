# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/download_data.py; python code/run_evaluation.py; python code/analyze_stability.py; 3 command(s) failed: python code/report_generator.py (rc=1); python -m pytest tests/unit/ (rc=1); python -m pytest tests/integration/test_pipeline.py (rc=1)

## Failing / missing run-book commands

- python code/download_data.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/download_data.py': [Errno 2] No such file or directory

- python code/run_evaluation.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/run_evaluation.py': [Errno 2] No such file or directory

- python code/analyze_stability.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/analyze_stability.py': [Errno 2] No such file or directory

- python code/report_generator.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/report_generator.py", line 16, in <module>
    from code.config import RESULTS_DIR, STABILITY_METRICS_FILE, CORRELATION_RESULTS_FILE, PERMUTATION_RESULTS_FILE
ImportError: cannot import name 'STABILITY_METRICS_FILE' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/config.py)

- python -m pytest tests/unit/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/.venv/bin/python: No module named pytest

- python -m pytest tests/integration/test_pipeline.py -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-264-assessing-the-stability-of-statistical-m/code/.venv/bin/python: No module named pytest

