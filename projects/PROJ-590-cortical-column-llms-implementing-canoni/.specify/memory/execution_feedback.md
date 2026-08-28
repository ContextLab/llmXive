# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ents.baseline_runner. It generates synthetic data for training (Loren…”
- code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ed(args.seed)          # Generate synthetic datasets     logger.info…”
- code/scripts/verify_gradient_logging.py: synthetic/fake INPUT data not authorized by the spec — “…ters.")      # 2. Create dummy input and target     batch_siz…”
- code/src/experiments/microcircuit_runner.py: synthetic/fake INPUT data not authorized by the spec — “…e_data(self):         """Generate synthetic training and test data."…”
- code/src/experiments/microcircuit_runner.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic data...")         train_data…”
- code/src/experiments/scaling.py: synthetic/fake INPUT data not authorized by the spec — “…aling study")          # Generate synthetic training and test data…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python -m src.training.trainer --config data/configs/baseline.yaml --output data/results/baseline_run.json`
- `python -m src.training.trainer --config data/configs/microcircuit.yaml --output data/results/microcircuit_run.json`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ents.baseline_runner. It generates synthetic data for training (Loren…”; code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ed(args.seed)          # Generate synthetic datasets     logger.info…”; code/scripts/verify_gradient_logging.py: synthetic/fake INPUT data not authorized by the spec — “…ters.")      # 2. Create dummy input and target     batch_siz…”; 6 command(s) failed: python -m src.training.trainer --config data/configs/baseline.yaml --output data/results/baseline_run.json (rc=1); python -m src.training.trainer --config data/configs/microcircuit.yaml --output data/results/microcircuit_run.json (rc=1); python -m src.experiments.ablation --variant ablation_recurrence --output data/results/ablation_recurrence.json (rc=1); 4 declared deliverable(s) absent: data/results/cost_curve_data.csv; data/results/cost_metrics.json; data/results/scaling_law.csv

## Failing / missing run-book commands

- python -m src.training.trainer --config data/configs/baseline.yaml --output data/results/baseline_run.json -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/src/training/trainer.py", line 1, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python -m src.training.trainer --config data/configs/microcircuit.yaml --output data/results/microcircuit_run.json -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/src/training/trainer.py", line 1, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python -m src.experiments.ablation --variant ablation_recurrence --output data/results/ablation_recurrence.json -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/src/experiments/ablation.py", line 1, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python -m src.experiments.scaling --variant scaling_2x --output data/results/scaling_2x.json -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/code/.venv/bin/python: No module named src.experiments.scaling
- python -m src.experiments.scaling --variant scaling_4x --output data/results/scaling_4x.json -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/code/.venv/bin/python: No module named src.experiments.scaling
- python scripts/run_all_experiments.sh --seed 12345 -> rc=2
    /home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/scripts/run_all_experiments.sh': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/results/cost_curve_data.csv
- data/results/cost_metrics.json
- data/results/scaling_law.csv
- data/results/test_data_polynomial.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/cost_curve_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/experiments/cost_analyzer.py` — NOT invoked by the run-book
    - `code/src/utils/report_generator.py` — NOT invoked by the run-book
    - `code/src/utils/cost_curve_generator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_cost_curve_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/cost_curve_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/cost_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/experiments/cost_analyzer.py` — NOT invoked by the run-book
    - `code/src/utils/report_generator.py` — NOT invoked by the run-book
    - `code/tests/integration/test_cost_analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/cost_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/scaling_law.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/experiments/scaling.py` — NOT invoked by the run-book
    - `code/src/experiments/cost_analyzer.py` — NOT invoked by the run-book
    - `code/src/utils/scaling_analyzer.py` — NOT invoked by the run-book
    - `code/src/utils/report_generator.py` — NOT invoked by the run-book
    - `code/src/utils/cost_curve_generator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_scaling_analyzer.py` — NOT invoked by the run-book
    - `code/tests/integration/test_scaling_law_verification.py` — NOT invoked by the run-book
    - `code/tests/integration/test_cost_analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/scaling_law.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/test_data_polynomial.npy` is declared but was NOT written. Scripts referencing it:
    - `code/src/experiments/baseline_runner.py` — NOT invoked by the run-book
    - `code/tests/integration/test_baseline_validation.py` — NOT invoked by the run-book
    - `code/scripts/generate_test_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/test_data_polynomial.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
