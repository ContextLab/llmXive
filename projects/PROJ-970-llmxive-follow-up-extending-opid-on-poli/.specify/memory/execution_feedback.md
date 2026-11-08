# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_graph_suite.py: synthetic/fake INPUT data not authorized by the spec — “…""" Batch‑generate synthetic State‑Graph environments…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_graph_suite.py: synthetic/fake INPUT data not authorized by the spec — “…""" Batch‑generate synthetic State‑Graph environments…”; 6 command(s) failed: python -m src.environment.graph_generator --output data/raw/synthetic_graphs (rc=1); python -m src.simulation.runner --config src/config.py --output data/processed/episode_results.csv (rc=1); python -m src.analysis.aggregation --input data/processed/episode_results.csv --output data/processed/aggregated_metrics.csv (rc=1); 2 declared deliverable(s) absent: data/processed/episode_results.csv; data/raw/graph_manifest.csv

## Failing / missing run-book commands

- python -m src.environment.graph_generator --output data/raw/synthetic_graphs -> rc=1
s
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/__init__.py", line 16, in <module>
    agent = _load_submodule('agent')
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/__init__.py", line 13, in _load_submodule
    return import_module(f'src.{name}')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/agent/__init__.py", line 9, in <module>
    from .opid_router import OPIDRouter, OPIDRouterConfig, main as opid_router_main  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'main' from 'src.agent.opid_router' (/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/agent/opid_router.py)

- python -m src.simulation.runner --config src/config.py --output data/processed/episode_results.csv -> rc=1
s
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/__init__.py", line 16, in <module>
    agent = _load_submodule('agent')
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/__init__.py", line 13, in _load_submodule
    return import_module(f'src.{name}')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/agent/__init__.py", line 9, in <module>
    from .opid_router import OPIDRouter, OPIDRouterConfig, main as opid_router_main  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'main' from 'src.agent.opid_router' (/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/agent/opid_router.py)

- python -m src.analysis.aggregation --input data/processed/episode_results.csv --output data/processed/aggregated_metrics.csv -> rc=1
s
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/__init__.py", line 16, in <module>
    agent = _load_submodule('agent')
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/__init__.py", line 13, in _load_submodule
    return import_module(f'src.{name}')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/agent/__init__.py", line 9, in <module>
    from .opid_router import OPIDRouter, OPIDRouterConfig, main as opid_router_main  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'main' from 'src.agent.opid_router' (/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/agent/opid_router.py)

- python -m src.analysis.regression --input data/processed/aggregated_metrics.csv -> rc=1
s
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/__init__.py", line 16, in <module>
    agent = _load_submodule('agent')
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/__init__.py", line 13, in _load_submodule
    return import_module(f'src.{name}')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/agent/__init__.py", line 9, in <module>
    from .opid_router import OPIDRouter, OPIDRouterConfig, main as opid_router_main  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'main' from 'src.agent.opid_router' (/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/agent/opid_router.py)

- python -m pytest tests/unit/ -v -> rc=2
/Python/3.11.18/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
src/__init__.py:16: in <module>
    agent = _load_submodule('agent')
src/__init__.py:13: in _load_submodule
    return import_module(f'src.{name}')
/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
src/agent/__init__.py:9: in <module>
    from .opid_router import OPIDRouter, OPIDRouterConfig, main as opid_router_main  # noqa: F401
E   ImportError: cannot import name 'main' from 'src.agent.opid_router' (/home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/src/agent/opid_router.py)
=========================== short test summary info ============================
ERROR tests/unit/test_graph_generator.py
ERROR tests/unit/test_metrics.py
ERROR tests/unit/test_policy.py
ERROR tests/unit/test_profile_sweep.py
ERROR tests/unit/test_seed.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 0.41s ===============================


- python -m pytest tests/integration/test_full_loop.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.18, pytest-8.1.1, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-970-llmxive-follow-up-extending-opid-on-poli/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli
configfile: pyproject.toml
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_full_loop.py



## Declared deliverables still missing

- data/processed/episode_results.csv
- data/raw/graph_manifest.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/episode_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/analysis/success_rate.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/experiments/runner.py` — NOT invoked by the run-book
    - `code/experiments/sweep_logic.py` — NOT invoked by the run-book
    - `code/simulation/runner.py` — NOT invoked by the run-book
    - `code/src/analysis/__init__.py` — NOT invoked by the run-book
    - `code/tests/test_metrics_integration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/episode_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/graph_manifest.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_graph_suite.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/graph_manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
