# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py --step download_and_validate (rc=1); python code/main.py --step preprocess (rc=1); python code/main.py --step compute_metrics (rc=1)

## Failing / missing run-book commands

- python code/main.py --step download_and_validate -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 21, in <module>
    from data.download import download_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/download.py", line 15, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/main.py --step preprocess -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 21, in <module>
    from data.download import download_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/download.py", line 15, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/main.py --step compute_metrics -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 21, in <module>
    from data.download import download_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/download.py", line 15, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/main.py --step analyze -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 21, in <module>
    from data.download import download_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/download.py", line 15, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/main.py --step visualize -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 21, in <module>
    from data.download import download_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/download.py", line 15, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
