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

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 88 fabricated/simulated-result signal(s) — results are not real measurements: code/evaluation/metrics.py: metric `y_scores` assigned from an RNG draw (line 363); code/evaluation/plots.py: metric `y_scores` assigned from an RNG draw (line 348); code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…# No ground truth - use placeholder values             f1 = 0.0…”; 6 command(s) failed: python code/src/config.py --check (rc=1); python code/src/data/download_datasets.py (rc=1); python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05 (rc=2); 1 declared deliverable(s) absent: data/processed/results/simulation_snr.csv

## Failing / missing run-book commands

- python code/src/config.py --check -> rc=1
    ============================================================
Configuration Check
============================================================
✓ Configuration file exists: /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml
  Current size: 652 bytes (limit: 2048 bytes)
✓ Configuration file size is within limits
ERROR: Missing required key: base_paths
❌ FAIL: Configuration structure validation failed
- python code/src/data/download_datasets.py -> rc=1
    xpected checksum available for traffic. Verification skipped.
2026-07-14 02:16:26,438 - WARNING - No expected checksum available for synthetic_control_chart. Verification skipped.
2026-07-14 02:16:26,438 - INFO - ======================================================================
2026-07-14 02:16:26,438 - INFO - Download Summary:
2026-07-14 02:16:26,438 - INFO - ======================================================================
2026-07-14 02:16:26,438 - INFO -   electricity: ✗ FAILED
2026-07-14 02:16:26,438 - INFO -   traffic: ✗ FAILED
2026-07-14 02:16:26,438 - INFO -   synthetic_control_chart: ✗ FAILED
2026-07-14 02:16:26,438 - INFO -   pems_sf: ✗ FAILED
2026-07-14 02:16:26,438 - INFO - ======================================================================
2026-07-14 02:16:26,438 - INFO - Verification Summary:
2026-07-14 02:16:26,438 - INFO - ======================================================================
2026-07-14 02:16:26,438 - INFO -   electricity: ✗ FAILED
2026-07-14 02:16:26,438 - INFO -   traffic: ✗ FAILED
2026-07-14 02:16:26,438 - INFO -   synthetic_control_chart: ✗ FAILED
2026-07-14 02:16:26,438 - ERROR - ✗ Some downloads failed. Check error messages above.
- python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05 -> rc=2
    usage: synthetic_generator.py [-h] [--output OUTPUT] [--n-samples N_SAMPLES]
                              [--anomaly-type {point,contextual,collective}]
                              [--anomaly-start ANOMALY_START]
                              [--anomaly-end ANOMALY_END]
                              [--magnitude MAGNITUDE] [--seed SEED]
synthetic_generator.py: error: unrecognized arguments: --anomaly-rate 0.05
- python code/src/services/anomaly_detector.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/services/anomaly_detector.py", line 22, in <module>
    from models.dp_gmm import DPGMMModel, DPGMMConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py", line 21, in <module>
    from models.anomaly_score import AnomalyScore
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/anomaly_score.py", line 8, in <module>
    class AnomalyScore:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/anomaly_score.py", line 27, in AnomalyScore
    component_assignments: Optional[List[int]] = field(default=None)
                                    ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
- python code/src/evaluation/simulation.py -> rc=1
    2026-07-14 02:16:27,236 - INFO - Starting simulation study with seed=42, n_samples=1000
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/simulation.py", line 210, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/simulation.py", line 182, in main
    result = run_simulation_study(
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/simulation.py", line 95, in run_simulation_study
    signal_config = SignalConfig(
                    ^^^^^^^^^^^^^
TypeError: SignalConfig.__init__() got an unexpected keyword argument 'length'
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
