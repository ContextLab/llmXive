# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/download.py (rc=1); python code/train.py (rc=1); python code/importance.py (rc=1)

## Failing / missing run-book commands

- python code/download.py -> rc=1
2026-10-19 06:37:43,061 - INFO - Starting dataset download to data
2026-10-19 06:37:43,062 - INFO - Checking dataset availability: emre-ozgür/DEAP-EMG
2026-10-19 06:37:43,062 - ERROR - Failed to load dataset from HuggingFace: Repo id must use alphanumeric chars, '-', '_' or '.'. The name cannot start or end with '-' or '.' and the maximum length is 96: 'emre-ozgür/DEAP-EMG'.
2026-10-19 06:37:43,062 - ERROR - Dataset download failed: Repo id must use alphanumeric chars, '-', '_' or '.'. The name cannot start or end with '-' or '.' and the maximum length is 96: 'emre-ozgür/DEAP-EMG'.


- python code/train.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/train.py", line 27, in <module>
    from config import (
ImportError: cannot import name 'DATA_PROCESSED_DIR' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/config.py)

- python code/importance.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/importance.py", line 31, in <module>
    from code.config import CONFIG
ImportError: cannot import name 'CONFIG' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/config.py)

- python code/validate.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/validate.py", line 21, in <module>
    from config import CONFIG
ImportError: cannot import name 'CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/config.py)

- python code/report.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/report.py", line 24, in <module>
    from config import PROJECT_ROOT, DATA_PROCESSED_DIR, DATA_MODELS_DIR, DATA_RAW_DIR
ImportError: cannot import name 'DATA_PROCESSED_DIR' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/config.py)

- python code/train.py --subjects 1,2 --fast-mode -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/train.py", line 27, in <module>
    from config import (
ImportError: cannot import name 'DATA_PROCESSED_DIR' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-214-decoding-emotional-valence-from-facial-e/code/config.py)

