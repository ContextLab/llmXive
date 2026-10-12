# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/utils/checksum.py --download (rc=1); python code/evaluation/runner.py (rc=1); python code/evaluation/runner.py --sample-size 500 (rc=1)

## Failing / missing run-book commands

- python code/utils/checksum.py --download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-713-calibration-of-predictive-intervals-for-/code/utils/checksum.py", line 14, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-713-calibration-of-predictive-intervals-for-/code/utils/logger.py", line 10, in <module>
    from config import PROJECT_ROOT, LOG_DIR, LOG_LEVEL
ImportError: cannot import name 'LOG_LEVEL' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-713-calibration-of-predictive-intervals-for-/code/config.py)

- python code/evaluation/runner.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-713-calibration-of-predictive-intervals-for-/code/evaluation/runner.py", line 24, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-713-calibration-of-predictive-intervals-for-/code/utils/logger.py", line 10, in <module>
    from config import PROJECT_ROOT, LOG_DIR, LOG_LEVEL
ImportError: cannot import name 'LOG_LEVEL' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-713-calibration-of-predictive-intervals-for-/code/config.py)

- python code/evaluation/runner.py --sample-size 500 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-713-calibration-of-predictive-intervals-for-/code/evaluation/runner.py", line 24, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-713-calibration-of-predictive-intervals-for-/code/utils/logger.py", line 10, in <module>
    from config import PROJECT_ROOT, LOG_DIR, LOG_LEVEL
ImportError: cannot import name 'LOG_LEVEL' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-713-calibration-of-predictive-intervals-for-/code/config.py)

