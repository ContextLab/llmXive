# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python src/meta_analysis.py; python src/loo_controller.py; 3 command(s) failed: python src/data_acquisition.py --mode real --subset-size (rc=1); python src/preprocessing.py (rc=1); python code/src/differential_expression.py (rc=1)

## Failing / missing run-book commands

- python src/data_acquisition.py --mode real --subset-size -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/src/data_acquisition.py", line 15, in <module>
    from src.config import get_project_root, ensure_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/src/__init__.py", line 4, in <module>
    from .utils import (
ImportError: cannot import name 'calculate_checksum' from 'src.utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/src/utils.py)
- python src/preprocessing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/src/preprocessing.py", line 18, in <module>
    from src.config import get_project_root, ensure_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/src/__init__.py", line 4, in <module>
    from .utils import (
ImportError: cannot import name 'calculate_checksum' from 'src.utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/src/utils.py)
- python code/src/differential_expression.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/src/differential_expression.py", line 13, in <module>
    import rpy2.robjects as ro
ModuleNotFoundError: No module named 'rpy2'
- python src/meta_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/src/meta_analysis.py': [Errno 2] No such file or directory
- python src/loo_controller.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/src/loo_controller.py': [Errno 2] No such file or directory
