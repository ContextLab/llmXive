# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- src/experiments/ablation.py: self-declared fabricated metric — “…evaluation     mae = 0.05  # Dummy value for structure demonstration…”
- src/experiments/ablation.py: self-declared fabricated metric — “…# For now, we create a dummy result to demonstrate structure…”
- code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ents.baseline_runner. It generates synthetic data for training (Loren…”
- code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ed(args.seed)          # Generate synthetic datasets     logger.info…”
- code/scripts/verify_gradient_logging.py: synthetic/fake INPUT data not authorized by the spec — “…ters.")      # 2. Create dummy input and target     batch_siz…”
- code/src/experiments/microcircuit_runner.py: synthetic/fake INPUT data not authorized by the spec — “…e_data(self):         """Generate synthetic training and test data."…”
- code/src/experiments/microcircuit_runner.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic data...")         train_data…”
- scripts/verify_gradient_logging.py: synthetic/fake INPUT data not authorized by the spec — “…)          # Create dummy data     logger.info("Creatin…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 fabricated/simulated-result signal(s) — results are not real measurements: src/experiments/ablation.py: self-declared fabricated metric — “…evaluation     mae = 0.05  # Dummy value for structure demonstration…”; src/experiments/ablation.py: self-declared fabricated metric — “…# For now, we create a dummy result to demonstrate structure…”; code/scripts/run_baseline_training.py: synthetic/fake INPUT data not authorized by the spec — “…ents.baseline_runner. It generates synthetic data for training (Loren…”; 5 command(s) failed: python -m src.experiments.ablation --variant ablation_recurrence --output data/results/ablation_recurrence.json (rc=1); python -m src.experiments.scaling --variant scaling_2x --output data/results/scaling_2x.json (rc=1); python -m src.experiments.scaling --variant scaling_4x --output data/results/scaling_4x.json (rc=1); 5 declared deliverable(s) absent: data/logs/training_log.json; data/results/cost_curve_data.csv; data/results/cost_metrics.json

## Failing / missing run-book commands

- python -m src.experiments.ablation --variant ablation_recurrence --output data/results/ablation_recurrence.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/src/experiments/ablation.py", line 14, in <module>
    from src.models.hybrid_network import HybridNetwork
ModuleNotFoundError: No module named 'src.models.hybrid_network'

- python -m src.experiments.scaling --variant scaling_2x --output data/results/scaling_2x.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-590-cortical-column-llms-implementing-canoni/bin/python: No module named src.experiments.scaling

- python -m src.experiments.scaling --variant scaling_4x --output data/results/scaling_4x.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-590-cortical-column-llms-implementing-canoni/bin/python: No module named src.experiments.scaling

- python -m pytest tests/ -v --timeout=3600 -> rc=1
py", line 116, in parse
    self.optparser = self._getparser()
                     ^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/config/argparsing.py", line 133, in _getparser
    arggroup.add_argument(*n, **a)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/argparse.py", line 1473, in add_argument
    return self._add_action(action)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/argparse.py", line 1675, in _add_action
    action = super(_ArgumentGroup, self)._add_action(action)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/argparse.py", line 1487, in _add_action
    self._check_conflict(action)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/argparse.py", line 1624, in _check_conflict
    conflict_handler(action, confl_optionals)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/argparse.py", line 1633, in _handle_conflict_error
    raise ArgumentError(action, message % conflict_string)
argparse.ArgumentError: argument --timeout: conflicting option string: --timeout

- python scripts/run_all_experiments.sh --seed 12345 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-590-cortical-column-llms-implementing-canoni/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-590-cortical-column-llms-implementing-canoni/scripts/run_all_experiments.sh': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/logs/training_log.json
- data/results/cost_curve_data.csv
- data/results/cost_metrics.json
- data/results/scaling_law.csv
- data/results/test_data_polynomial.npy

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `scikit-learn` to the project's `requirements.txt` and `pip install scikit-learn`.
- **Verified**: this loads **200** real records with fields: input_features, target, function_name, train_test_split.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import numpy as np
from sklearn.datasets import make_regression
X, y = make_regression(n_samples=200, n_features=5, noise=0.1, random_state=0)
records = [{
    "input_features": list(map(float, X[i])),
    "target": float(y[i]),
    "function_name": "linear",
    "train_test_split": "train"
} for i in range(len(X))]
print(f"RECORDS={len(records)}")
print("FIELDS=input_features,target,function_name,train_test_split")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/training_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/utils/cost_curve_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/training_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/cost_curve_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/experiments/cost_analyzer.py` — NOT invoked by the run-book
    - `code/src/utils/cost_curve_generator.py` — NOT invoked by the run-book
    - `code/src/utils/report_generator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_cost_curve_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/cost_curve_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/cost_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_cost_analyzer.py` — NOT invoked by the run-book
    - `code/src/experiments/cost_analyzer.py` — NOT invoked by the run-book
    - `code/src/utils/report_generator.py` — NOT invoked by the run-book
    - `code/tests/integration/test_cost_analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/cost_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/scaling_law.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_scaling_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_scaling_law_verification.py` — NOT invoked by the run-book
    - `code/scripts/run_scaling_study.py` — NOT invoked by the run-book
    - `code/src/experiments/cost_analyzer.py` — NOT invoked by the run-book
    - `code/src/experiments/scaling.py` — NOT invoked by the run-book
    - `code/src/utils/report_generator.py` — NOT invoked by the run-book
    - `code/src/utils/scaling_analyzer.py` — NOT invoked by the run-book
    - `code/tests/integration/test_cost_analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/scaling_law.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/test_data_polynomial.npy` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_test_data.py` — NOT invoked by the run-book
    - `code/src/experiments/baseline_runner.py` — NOT invoked by the run-book
    - `code/tests/integration/test_baseline_validation.py` — NOT invoked by the run-book
    - `code/tests/unit/test_benchmarks.py` — NOT invoked by the run-book
    - `src/experiments/final_verification.py` — NOT invoked by the run-book
    - `scripts/generate_test_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/test_data_polynomial.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
