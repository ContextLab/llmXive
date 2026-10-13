# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): bash code/pipeline/run_pipeline.sh --data data/raw/ --out results/; bash code/pipeline/diagnostics.sh; 1 command(s) failed: python -m pytest tests/contract/test_schemas.py (rc=4)

## Failing / missing run-book commands

- python -c "import numpyro; print('NumPyro Ready')" -> rc=1
network-propagat/lib/python3.11/site-packages/numpyro/distributions/__init__.py", line 4, in <module>
    from numpyro.distributions.conjugate import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-074-statistical-modeling-of-network-propagat/lib/python3.11/site-packages/numpyro/distributions/conjugate.py", line 9, in <module>
    from numpyro.distributions.continuous import Beta, Dirichlet, Gamma
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-074-statistical-modeling-of-network-propagat/lib/python3.11/site-packages/numpyro/distributions/continuous.py", line 36, in <module>
    from jax.scipy.linalg import cho_solve, solve_triangular
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-074-statistical-modeling-of-network-propagat/lib/python3.11/site-packages/jax/scipy/linalg.py", line 18, in <module>
    from jax._src.scipy.linalg import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-074-statistical-modeling-of-network-propagat/lib/python3.11/site-packages/jax/_src/scipy/linalg.py", line 403, in <module>
    @_wraps(scipy.linalg.tril)
            ^^^^^^^^^^^^^^^^^
AttributeError: module 'scipy.linalg' has no attribute 'tril'

- bash code/pipeline/run_pipeline.sh --data data/raw/ --out results/ -> rc=-1

shell script must be an existing project-local .sh file
- bash code/pipeline/diagnostics.sh -> rc=-1

shell script must be an existing project-local .sh file
- python -m pytest tests/contract/test_schemas.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.0.0, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-074-statistical-modeling-of-network-propagat
plugins: platformdirs-4.13.0
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/test_schemas.py


