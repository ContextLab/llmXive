# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/inference/hybrid_sim.py: metric `latency_reduction` assigned from an RNG draw (line 206)
- code/models/gru_estimator.py: synthetic/fake INPUT data not authorized by the spec — “…n{model}")          # 3. Dummy Data Generation for Verificat…”
- code/utils/inference_optimizer.py: synthetic/fake INPUT data not authorized by the spec — “…...")          # Prepare dummy input based on sample data str…”
- code/utils/inference_optimizer.py: synthetic/fake INPUT data not authorized by the spec — “…al()          # Create a dummy input for tracing         # Sh…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/data/extract_turn_taking.py`
- `python code/data/fetch_data.py`
- `python code/metrics/calculate_fid_stability.py`
- `python code/metrics/statistical_tests.py`
- `python code/model/estimator_train.py`
- `python code/model/hybrid_simulate.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/inference/hybrid_sim.py: metric `latency_reduction` assigned from an RNG draw (line 206); code/models/gru_estimator.py: synthetic/fake INPUT data not authorized by the spec — “…n{model}")          # 3. Dummy Data Generation for Verificat…”; code/utils/inference_optimizer.py: synthetic/fake INPUT data not authorized by the spec — “…...")          # Prepare dummy input based on sample data str…”; 7 run-book script(s) missing (plan/impl path mismatch): python code/data/fetch_data.py; python code/data/extract_turn_taking.py; python code/model/estimator_train.py; 5 declared deliverable(s) absent: data/metrics/power_analysis_final.json; data/metrics/theoretical_defaults.json; data/processed/filtered.parquet

## Failing / missing run-book commands

- python code/data/fetch_data.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/data/fetch_data.py': [Errno 2] No such file or directory
- python code/data/extract_turn_taking.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/data/extract_turn_taking.py': [Errno 2] No such file or directory
- python code/model/estimator_train.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/model/estimator_train.py': [Errno 2] No such file or directory
- python code/model/hybrid_simulate.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/model/hybrid_simulate.py': [Errno 2] No such file or directory
- python code/metrics/calculate_fid_stability.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/metrics/calculate_fid_stability.py': [Errno 2] No such file or directory
- python code/metrics/statistical_tests.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/metrics/statistical_tests.py': [Errno 2] No such file or directory
- python code/utils/state_manager.py --update -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/utils/state_manager.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/metrics/power_analysis_final.json
- data/metrics/theoretical_defaults.json
- data/processed/filtered.parquet
- data/processed/raw_extract.parquet
- data/processed/sampled_dataset.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metrics/power_analysis_final.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/power_analysis_final.py` — NOT invoked by the run-book
    - `code/tasks/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/power_analysis_final.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/theoretical_defaults.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/power_analysis_initial.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/theoretical_defaults.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/power_analysis_initial.py` — NOT invoked by the run-book
    - `code/tasks/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/utils/validators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_extract.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/generate_power_analysis.py` — NOT invoked by the run-book
    - `code/data/extract_latents.py` — NOT invoked by the run-book
    - `code/tasks/validate_thresholds.py` — NOT invoked by the run-book
    - `code/tasks/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/tasks/calibrate_thresholds.py` — NOT invoked by the run-book
    - `code/tasks/power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_extract.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sampled_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/models/trainer.py` — NOT invoked by the run-book
    - `code/inference/hybrid_sim.py` — NOT invoked by the run-book
    - `code/inference/generate_counterfactual_indices.py` — NOT invoked by the run-book
    - `code/inference/fallback_handler.py` — NOT invoked by the run-book
    - `code/inference/fallback_logic_handler.py` — NOT invoked by the run-book
    - `code/data/validate_processed.py` — NOT invoked by the run-book
    - `code/data/power_analysis_final.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sampled_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
