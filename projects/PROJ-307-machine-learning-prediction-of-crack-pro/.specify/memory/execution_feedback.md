# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/main.py --step download (rc=1); python code/main.py --step preprocess (rc=1); python code/main.py --step baseline (rc=1)

## Failing / missing run-book commands

- python code/main.py --step download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 9, in <module>
    from data.loader import load_nasa_data, load_nist_data, validate_schema
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/data/loader.py", line 10, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'

- python code/main.py --step preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 9, in <module>
    from data.loader import load_nasa_data, load_nist_data, validate_schema
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/data/loader.py", line 10, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'

- python code/main.py --step baseline -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 9, in <module>
    from data.loader import load_nasa_data, load_nist_data, validate_schema
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/data/loader.py", line 10, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'

- python code/main.py --step augmented -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 9, in <module>
    from data.loader import load_nasa_data, load_nist_data, validate_schema
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/data/loader.py", line 10, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'

- python code/main.py --step regimes -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 9, in <module>
    from data.loader import load_nasa_data, load_nist_data, validate_schema
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/data/loader.py", line 10, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'

- python code/main.py --step full -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 9, in <module>
    from data.loader import load_nasa_data, load_nist_data, validate_schema
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/data/loader.py", line 10, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'

- python -m pytest tests/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/.venv/bin/python: No module named pytest

