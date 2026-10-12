# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): bash code/pipeline/run_pipeline.sh --data data/raw/ --out results/; bash code/pipeline/diagnostics.sh; 1 command(s) failed: python -m pytest tests/contract/test_schemas.py (rc=4)

## Failing / missing run-book commands

- python -c "import numpyro; print('NumPyro Ready')" -> rc=1
", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-074-statistical-modeling-of-network-propagat/lib/python3.11/site-packages/numpyro/__init__.py", line 6, in <module>
    from numpyro import compat, diagnostics, distributions, handlers, infer, ops, optim
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-074-statistical-modeling-of-network-propagat/lib/python3.11/site-packages/numpyro/infer/__init__.py", line 5, in <module>
    from numpyro.infer.elbo import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-074-statistical-modeling-of-network-propagat/lib/python3.11/site-packages/numpyro/infer/elbo.py", line 25, in <module>
    from numpyro.ops.provenance import eval_provenance
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-074-statistical-modeling-of-network-propagat/lib/python3.11/site-packages/numpyro/ops/provenance.py", line 7, in <module>
    from jax.experimental.pjit import pjit_p
ImportError: cannot import name 'pjit_p' from 'jax.experimental.pjit' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-074-statistical-modeling-of-network-propagat/lib/python3.11/site-packages/jax/experimental/pjit.py)

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


