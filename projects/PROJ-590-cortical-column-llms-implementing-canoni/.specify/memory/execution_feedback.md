# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ents.baseline_runner. It generates synthetic data for training (Loren…”
- code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ed(args.seed)          # Generate synthetic datasets     logger.info…”
- code/src/experiments/microcircuit_runner.py: synthetic/fake INPUT data not authorized by the spec — “…e_data(self):         """Generate synthetic training and test data."…”
- code/src/experiments/microcircuit_runner.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic data...")         train_data…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/data/benchmarks.py --output data/raw_function_data.json --seed 42`
  - script usage: `benchmarks.py [-h] --type {lorenz,fourier,polynomial} [--seed SEED]`
  - argparse error: `benchmarks.py: error: the following arguments are required: --type`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ents.baseline_runner. It generates synthetic data for training (Loren…”; code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ed(args.seed)          # Generate synthetic datasets     logger.info…”; code/src/experiments/microcircuit_runner.py: synthetic/fake INPUT data not authorized by the spec — “…e_data(self):         """Generate synthetic training and test data."…”; 5 command(s) failed: python src/data/benchmarks.py --output data/raw_function_data.json --seed 42 (rc=2); python -m src.experiments.ablation --variant ablation_recurrence --output data/results/ablation_recurrence.json (rc=1); python -m src.experiments.scaling --variant scaling_2x --output data/results/scaling_2x.json (rc=1); 2 declared deliverable(s) absent: data/logs/gradient_norms.json; data/results/test_data_polynomial.npy

## Failing / missing run-book commands

- python src/data/benchmarks.py --output data/raw_function_data.json --seed 42 -> rc=2
    usage: benchmarks.py [-h] --type {lorenz,fourier,polynomial} [--seed SEED]
                     [--n-samples N_SAMPLES] [--n-features N_FEATURES]
                     [--noise NOISE] [--output-dir OUTPUT_DIR]
                     [--prefix PREFIX]
benchmarks.py: error: the following arguments are required: --type
- python -m src.experiments.ablation --variant ablation_recurrence --output data/results/ablation_recurrence.json -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/src/experiments/ablation.py", line 14, in <module>
    from src.models.hybrid_network import HybridNetwork
ModuleNotFoundError: No module named 'src.models.hybrid_network'
- python -m src.experiments.scaling --variant scaling_2x --output data/results/scaling_2x.json -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/code/.venv/bin/python: No module named src.experiments.scaling
- python -m src.experiments.scaling --variant scaling_4x --output data/results/scaling_4x.json -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/code/.venv/bin/python: No module named src.experiments.scaling
- python scripts/run_all_experiments.sh --seed 12345 -> rc=2
    /home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/scripts/run_all_experiments.sh': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/logs/gradient_norms.json
- data/results/test_data_polynomial.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/gradient_norms.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/training/homeostasis.py` — NOT invoked by the run-book
    - `code/src/training/trainer.py` — NOT invoked by the run-book
    - `code/src/experiments/microcircuit_runner.py` — NOT invoked by the run-book
    - `code/src/utils/statistics.py` — NOT invoked by the run-book
    - `code/tests/unit/test_statistics.py` — NOT invoked by the run-book
    - `code/tests/unit/test_homeostasis.py` — NOT invoked by the run-book
    - `code/tests/unit/test_homeostasis_scaling_hook.py` — NOT invoked by the run-book
    - `code/tests/integration/test_scaling_experiment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/gradient_norms.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/test_data_polynomial.npy` is declared but was NOT written. Scripts referencing it:
    - `code/src/experiments/baseline_runner.py` — NOT invoked by the run-book
    - `code/src/data/benchmarks.py` — NOT invoked by the run-book
    - `code/tests/integration/test_baseline_validation.py` — NOT invoked by the run-book
    - `code/scripts/generate_test_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/test_data_polynomial.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
