# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --stage preprocess (rc=1); python code/main.py --stage metrics (rc=1); python code/main.py --stage analysis (rc=1)

## Failing / missing run-book commands

- python code/main.py --stage preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
ImportError: cannot import name 'main' from 'metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py)

- python code/main.py --stage metrics -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
ImportError: cannot import name 'main' from 'metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py)

- python code/main.py --stage analysis -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
ImportError: cannot import name 'main' from 'metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py)

- python code/main.py --stage report -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
ImportError: cannot import name 'main' from 'metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py)

