# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 13 run-book script(s) missing (plan/impl path mismatch): bash data/download.sh; bash data/verify.sh   # exits with code 1 if `probability_value` missing; python analysis/baseline/align.py; 3 command(s) failed: python -m pytest tests/unit/ (rc=4); python -m pytest tests/integration/ (rc=4); python -m pytest tests/contract/ (rc=4)

## Failing / missing run-book commands

- bash data/download.sh -> rc=-1

shell script must be an existing project-local .sh file
- bash data/verify.sh   # exits with code 1 if `probability_value` missing -> rc=-1

shell script must be an existing project-local .sh file
- python analysis/baseline/align.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/baseline/align.py': [Errno 2] No such file or directory

- python analysis/baseline/metrics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/baseline/metrics.py': [Errno 2] No such file or directory

- python analysis/baseline/plots.py   # creates reliability_diagram_raw.png, pit_histogram_raw.png -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/baseline/plots.py': [Errno 2] No such file or directory

- python analysis/isotonic/train.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/isotonic/train.py': [Errno 2] No such file or directory

- python analysis/isotonic/evaluate.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/isotonic/evaluate.py': [Errno 2] No such file or directory

- python analysis/isotonic/sensitivity.py   # runs 60/40 and 80/20 splits -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/isotonic/sensitivity.py': [Errno 2] No such file or directory

- python analysis/bayesian/model.py          # may fall back to isotonic -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/bayesian/model.py': [Errno 2] No such file or directory

- python analysis/bayesian/prior_sensitivity.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/bayesian/prior_sensitivity.py': [Errno 2] No such file or directory

- python analysis/bayesian/diagnostics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/bayesian/diagnostics.py': [Errno 2] No such file or directory

- python analysis/comparison/diebold_mariano.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/comparison/diebold_mariano.py': [Errno 2] No such file or directory

- python analysis/comparison/summary.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/comparison/summary.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/


- python -m pytest tests/integration/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/


- python -m pytest tests/contract/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/


