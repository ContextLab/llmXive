# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/evaluation/metrics.py: metric `y_scores` assigned from an RNG draw (line 363)
- code/evaluation/plots.py: metric `y_scores` assigned from an RNG draw (line 348)
- code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…# No ground truth - use placeholder values             f1 = 0.0…”
- code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…())                  # Return placeholder result         return EvaluationResu…”
- code/scripts/verify_confusion_matrix.py: metric `y_scores` assigned from an RNG draw (line 50)
- code/src/data/synthetic_generator.py: metric `duration` assigned from an RNG draw (line 196)
- code/src/data/synthetic_generator.py: metric `duration` assigned from an RNG draw (line 242)
- code/src/evaluation/metrics.py: metric `y_scores` assigned from an RNG draw (line 363)

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 90 fabricated/simulated-result signal(s) — results are not real measurements: code/evaluation/metrics.py: metric `y_scores` assigned from an RNG draw (line 363); code/evaluation/plots.py: metric `y_scores` assigned from an RNG draw (line 348); code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…# No ground truth - use placeholder values             f1 = 0.0…”; 6 command(s) failed: python code/src/config.py --check (rc=1); python code/src/data/download_datasets.py (rc=1); python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05 (rc=1); 1 declared deliverable(s) absent: data/processed/results/simulation_snr.csv

## Failing / missing run-book commands

- python code/src/config.py --check -> rc=1
    ============================================================
Configuration Check
============================================================
✓ Configuration file exists: /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml
  Current size: 653 bytes (limit: 2048 bytes)
✓ Configuration file size is within limits
ERROR: Missing required key: base_paths
❌ FAIL: Configuration structure validation failed
- python code/src/data/download_datasets.py -> rc=1
    2026-07-14 12:28:35,962 - INFO - Downloading https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt to data/raw/electricity_load.csv
2026-07-14 12:28:36,330 - ERROR - Download failed: HTTP Error 404: Not Found
2026-07-14 12:28:36,348 - INFO - Downloading https://pems.dot.ca.gov/data/traffic_data.csv to data/raw/traffic_data.csv
2026-07-14 12:28:36,577 - ERROR - Download failed: HTTP Error 404: Not Found
2026-07-14 12:28:36,595 - INFO - Downloading https://archive.ics.uci.edu/ml/machine-learning-databases/00258/synthetic_control.data to data/raw/synthetic_control.csv
2026-07-14 12:28:36,820 - ERROR - Download failed: HTTP Error 404: Not Found
2026-07-14 12:28:36,821 - INFO - Download Summary: 0/3 datasets successful
2026-07-14 12:28:36,821 - ERROR - 
✗ Some datasets failed download or verification.
- python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05 -> rc=1
    /code/src/data/synthetic_generator.py", line 490, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/data/synthetic_generator.py", line 480, in main
    dataset = generate_synthetic_timeseries(signal_config, anomaly_config, args.length)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/data/synthetic_generator.py", line 296, in generate_synthetic_timeseries
    values, ground_truth = inject_collective_anomalies(values, anomaly_config, ground_truth)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/data/synthetic_generator.py", line 242, in inject_collective_anomalies
    duration = np.random.randint(config.anomaly_duration_min * 2, config.anomaly_duration_max * 2 + 1)
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'AnomalyConfig' object has no attribute 'anomaly_duration_min'
- python code/src/services/anomaly_detector.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/services/anomaly_detector.py", line 24, in <module>
    from models.anomaly_score import AnomalyScore
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/__init__.py", line 5, in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dp_gmm.py", line 125, in <module>
    import _winapi
ModuleNotFoundError: No module named '_winapi'
- python code/src/evaluation/simulation.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/simulation.py", line 27, in <module>
    from src.models.dpgmm import DPGMMModel, DPGMMConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/__init__.py", line 5, in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dp_gmm.py", line 125, in <module>
    import _winapi
ModuleNotFoundError: No module named '_winapi'
- python code/src/evaluation/robustness.py --subset-size 50 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/robustness.py", line 36, in <module>
    from src.models.dpgmm import DPGMMModel, DPGMMConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/__init__.py", line 5, in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dp_gmm.py", line 125, in <module>
    import _winapi
ModuleNotFoundError: No module named '_winapi'

## Declared deliverables still missing

- data/processed/results/simulation_snr.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `AnomalyConfig` (in `code/src/data/synthetic_generator.py`) — accessed via method/attribute names this round: `anomaly_duration_min`

`AnomalyConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/src/data/synthetic_generator.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `AnomalyConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`AnomalyConfig.anomaly_duration_min` call sites (0):

### class `SignalConfig` (in `code/src/data/synthetic_generator.py`) — accessed via method/attribute names this round: `__init__`

`SignalConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/src/data/synthetic_generator.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `SignalConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`SignalConfig.__init__` call sites (1):
- code/src/baselines/lstm_ae.py: super().__init__()

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/results/simulation_snr.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/evaluation/simulation.py` — IS a run-book command
    - `code/src/simulation/ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results/simulation_snr.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
