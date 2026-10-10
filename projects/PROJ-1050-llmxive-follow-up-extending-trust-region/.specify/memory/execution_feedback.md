# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/student/policy.py: function `select_action` returns a bare RNG draw (line 37) — a reported value computed from no real input

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/student/policy.py: function `select_action` returns a bare RNG draw (line 37) — a reported value computed from no real input; 4 command(s) failed: python -m experiments.runner --debug --alpha 0.5 --horizon 4 --seed 42 (rc=1); python -m experiments.runner --grid (rc=1); python -m analysis.two_part_model --input data/raw/episodes_*.parquet (rc=1); 1 declared deliverable(s) absent: data/processed/collapse_sweep.csv

## Failing / missing run-book commands

- python -m experiments.runner --debug --alpha 0.5 --horizon 4 --seed 42 -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code/experiments/__init__.py", line 5, in <module>
    from .runner import run_training_loop
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code/experiments/runner.py", line 23, in <module>
    from env.reasoning_mdp import ReasoningMDP
ModuleNotFoundError: No module named 'env'

- python -m experiments.runner --grid -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code/experiments/__init__.py", line 5, in <module>
    from .runner import run_training_loop
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code/experiments/runner.py", line 23, in <module>
    from env.reasoning_mdp import ReasoningMDP
ModuleNotFoundError: No module named 'env'

- python -m analysis.two_part_model --input data/raw/episodes_*.parquet -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code/analysis/__init__.py", line 4, in <module>
    from .tobit_model import TobitModel
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code/analysis/tobit_model.py", line 6, in <module>
    from statsmodels.regression.tobit import Tobit
ModuleNotFoundError: No module named 'statsmodels.regression.tobit'

- python -m analysis.plot_results --input data/processed/results_*.csv --output docs/results/collapse_plot.png -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code/analysis/__init__.py", line 4, in <module>
    from .tobit_model import TobitModel
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code/analysis/tobit_model.py", line 6, in <module>
    from statsmodels.regression.tobit import Tobit
ModuleNotFoundError: No module named 'statsmodels.regression.tobit'


## Declared deliverables still missing

- data/processed/collapse_sweep.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/collapse_sweep.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/nonmonotonicity_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/collapse_sweep.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
