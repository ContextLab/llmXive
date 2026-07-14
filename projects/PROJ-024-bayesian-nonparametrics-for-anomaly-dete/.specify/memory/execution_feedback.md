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
- code/src/evaluation/metrics.py: metric `y_scores` assigned from an RNG draw (line 363)
- code/src/evaluation/plots.py: metric `y_scores` assigned from an RNG draw (line 348)
- code/src/services/threshold_calibrator.py: metric `normal_scores` assigned from an RNG draw (line 418)

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 87 fabricated/simulated-result signal(s) — results are not real measurements: code/evaluation/metrics.py: metric `y_scores` assigned from an RNG draw (line 363); code/evaluation/plots.py: metric `y_scores` assigned from an RNG draw (line 348); code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…# No ground truth - use placeholder values             f1 = 0.0…”; 5 command(s) failed: python code/src/config.py --check (rc=1); python code/src/data/download_datasets.py (rc=1); python code/src/services/anomaly_detector.py (rc=1); 1 declared deliverable(s) absent: data/processed/results/simulation_snr.csv

## Failing / missing run-book commands

- python code/src/config.py --check -> rc=1
    ============================================================
Configuration Check
============================================================
ERROR: Configuration file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/code/config.yaml
- python code/src/data/download_datasets.py -> rc=1
    2026-07-14 17:25:54,559 - INFO - ============================================================
2026-07-14 17:25:54,559 - INFO - Dataset Download Script (T052)
2026-07-14 17:25:54,559 - INFO - ============================================================
2026-07-14 17:25:54,559 - WARNING - Search result file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/processed/results/search_results.json. Assuming search failed.
2026-07-14 17:25:54,559 - CRITICAL - Aborting download. T052b Search failed: Search result file missing
2026-07-14 17:25:54,559 - INFO - Download manifest saved to /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/processed/results/download_manifest.json
2026-07-14 17:25:54,559 - ERROR - No datasets were successfully downloaded.
- python code/src/services/anomaly_detector.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/services/anomaly_detector.py", line 25, in <module>
    from models.dpgmm import DPGMMModel, DPGMMConfig
ModuleNotFoundError: No module named 'models.dpgmm'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/services/anomaly_detector.py", line 32, in <module>
    from models.dpgmm import DPGMMModel, DPGMMConfig
ModuleNotFoundError: No module named 'models.dpgmm'
- python code/src/evaluation/simulation.py -> rc=1
    'stride': 1, 'noise_level': 0.1, 'anomaly_amplitude': 2.0, 'anomaly_duration': 10, 'seed': 42, 'alpha_true': 1.0, 'alpha_anomaly': 3.0}
2026-07-14 17:25:55,182 - INFO - Generated signal of length 2500 with 160 anomaly points
2026-07-14 17:25:55,183 - INFO - Extracted 2451 windows
2026-07-14 17:25:55,219 - INFO - Estimated noise std: 0.0649
2026-07-14 17:25:55,244 - INFO - Simulation completed in 0.06 seconds
2026-07-14 17:25:55,263 - INFO - Results saved to /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/data/processed/results/simulation_snr.csv
2026-07-14 17:25:55,264 - INFO - Anomaly window SNR stats: mean=0.1726, min=0.0000
2026-07-14 17:25:55,264 - INFO - SNR > 1 passing rate: 5.22% (46/881)
2026-07-14 17:25:55,264 - WARNING - VALIDATION FAILED: SNR <= 1 for majority of anomaly windows
2026-07-14 17:25:55,264 - INFO - ============================================================
2026-07-14 17:25:55,264 - INFO - SIMULATION VALIDATION: FAILED
2026-07-14 17:25:55,264 - INFO - The ADVI estimator may need tuning before proceeding to Phase 3.
2026-07-14 17:25:55,264 - INFO - ============================================================
- python code/src/evaluation/robustness.py --subset-size 50 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/robustness.py", line 32, in <module>
    from models.dp_gmm import DPGMMModel, DPGMMConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py", line 21, in <module>
    from models.anomaly_score import AnomalyScore
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/anomaly_score.py", line 8, in <module>
    class AnomalyScore:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/anomaly_score.py", line 27, in AnomalyScore
    component_assignments: Optional[List[int]] = field(default=None)
                                    ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

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

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/processed/results/search_results.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/src/data/download_datasets.py`, `code/tests/unit/test_download_datasets.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/processed/results/search_results.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/src/data/download_datasets.py`, `code/tests/unit/test_download_datasets.py`.
