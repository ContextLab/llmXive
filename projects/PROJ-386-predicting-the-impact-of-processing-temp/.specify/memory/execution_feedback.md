# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py --sample-size 100 --timeout 3600 (rc=1); python code/main.py (rc=1)

## Failing / missing run-book commands

- python code/main.py --sample-size 100 --timeout 3600 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/main.py", line 18, in <module>
    from config import GITHUB_ACTIONS_TIMEOUT, DATA_RAW_PATH, DATA_PROCESSED_PATH, ARTIFACTS_PATH
ImportError: cannot import name 'DATA_RAW_PATH' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/config.py)
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/main.py", line 18, in <module>
    from config import GITHUB_ACTIONS_TIMEOUT, DATA_RAW_PATH, DATA_PROCESSED_PATH, ARTIFACTS_PATH
ImportError: cannot import name 'DATA_RAW_PATH' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-386-predicting-the-impact-of-processing-temp/code/config.py)
