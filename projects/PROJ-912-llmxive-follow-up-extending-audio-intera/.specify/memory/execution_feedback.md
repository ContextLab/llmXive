# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/inference/logging_utils.py: self-declared fabricated metric — “…latency = 100.0 + (i * 10)  # Simulated latency                  batch_log =…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/inference/logging_utils.py: self-declared fabricated metric — “…latency = 100.0 + (i * 10)  # Simulated latency                  batch_log =…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/models/compress.py  --teacher facebook/wav2vec2-base-960h  --configs int,int4  --pruning-ratios,0.2  --distill  --calibration-data data/processed/subtle_cue_manifest.json; 4 command(s) failed: python code/inference/runner.py  --model-dir models/checkpoints/  --testbed data/processed/subtle_cue_manifest.json  --thresholds,0.05,0.1 (rc=1); python code/analysis/robustness_curve.py --input results/metrics.csv --output results/robustness_curve.png (rc=1); python code/analysis/sensitivity.py --input results/metrics.csv --output results/sensitivity_report.json (rc=1); 5 declared deliverable(s) absent: data/processed/ablation_logits.parquet; data/processed/breaking_point.json; data/processed/robustness_curve.png

## Failing / missing run-book commands

- python code/models/compress.py  --teacher facebook/wav2vec2-base-960h  --configs int,int4  --pruning-ratios,0.2  --distill  --calibration-data data/processed/subtle_cue_manifest.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/models/compress.py': [Errno 2] No such file or directory
- python code/inference/runner.py  --model-dir models/checkpoints/  --testbed data/processed/subtle_cue_manifest.json  --thresholds,0.05,0.1 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/inference/runner.py", line 15, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'
- python code/analysis/robustness_curve.py --input results/metrics.csv --output results/robustness_curve.png -> rc=1
    xtending-audio-intera/data/processed/correlation_data.json

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/robustness_curve.py", line 261, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/robustness_curve.py", line 253, in main
    result = run_analysis()
             ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/robustness_curve.py", line 231, in run_analysis
    correlation_data = load_correlation_data(correlation_path)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/robustness_curve.py", line 128, in load_correlation_data
    raise LlmXiveError(f"Correlation data file not found: {input_path}")
utils.logger.LlmXiveError: Correlation data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/data/processed/correlation_data.json
- python code/analysis/sensitivity.py --input results/metrics.csv --output results/sensitivity_report.json -> rc=1
    s.csv"
                   ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'PathConfig' object has no attribute 'processed_data_dir'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/sensitivity.py", line 200, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/sensitivity.py", line 183, in main
    results = run_sensitivity_analysis()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/sensitivity.py", line 125, in run_sensitivity_analysis
    metrics = load_robustness_metrics()
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/sensitivity.py", line 38, in load_robustness_metrics
    metrics_path = config.processed_data_dir / "robustness_metrics.csv"
                   ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'PathConfig' object has no attribute 'processed_data_dir'. Did you mean: 'processed_dir'?
- python code/analysis/ablation.py --input results/metrics.csv --output results/ablation_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/code/analysis/ablation.py", line 15, in <module>
    from models.student import clone_model, freeze_attention_heads, prune_ffn_layers
ModuleNotFoundError: No module named 'models'

## Declared deliverables still missing

- data/processed/ablation_logits.parquet
- data/processed/breaking_point.json
- data/processed/robustness_curve.png
- data/processed/robustness_metrics.csv
- data/processed/sensitivity_report.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `PathConfig` (in `code/config.py`) — accessed via method/attribute names this round: `processed_data_dir`

`PathConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `PathConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`PathConfig.processed_data_dir` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/ablation_logits.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/ablation.py` — IS a run-book command
    - `code/inference/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ablation_logits.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/breaking_point.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/linters.py` — NOT invoked by the run-book
    - `code/analysis/robustness_curve.py` — IS a run-book command
    - `code/analysis/generate_reports.py` — NOT invoked by the run-book
    - `code/analysis/validate_descriptive_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/breaking_point.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_curve.png` is declared but was NOT written. Scripts referencing it:
    - `code/utils/linters.py` — NOT invoked by the run-book
    - `code/analysis/generate_reports.py` — NOT invoked by the run-book
    - `code/analysis/validate_descriptive_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_curve.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/robustness_curve.py` — IS a run-book command
    - `code/analysis/sensitivity.py` — IS a run-book command
    - `code/analysis/generate_reports.py` — NOT invoked by the run-book
    - `code/analysis/validate_descriptive_results.py` — NOT invoked by the run-book
    - `code/inference/integrate_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/linters.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — IS a run-book command
    - `code/analysis/generate_reports.py` — NOT invoked by the run-book
    - `code/analysis/validate_descriptive_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/data/processed/correlation_data.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis/robustness_curve.py`, `code/analysis/generate_reports.py`, `code/analysis/validate_descriptive_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-912-llmxive-follow-up-extending-audio-intera/data/processed/correlation_data.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis/robustness_curve.py`, `code/analysis/generate_reports.py`, `code/analysis/validate_descriptive_results.py`.
