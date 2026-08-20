# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/data/profiles.py: synthetic/fake INPUT data not authorized by the spec — “…}")             # Create mock data for testing if fetch fai…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/data/profiles.py: synthetic/fake INPUT data not authorized by the spec — “…}")             # Create mock data for testing if fetch fai…”; 2 command(s) failed: python code/scripts/run_pipeline.py --stage fetch (rc=1); python code/scripts/run_pipeline.py (rc=1); 7 declared deliverable(s) absent: data/baseline_results.csv; data/permutation_results.csv; data/profiling_logs.json

## Failing / missing run-book commands

- python code/scripts/run_pipeline.py --stage fetch -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi/code/scripts/run_pipeline.py", line 10, in <module>
    from src.models.evaluate import main as evaluate_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi/code/src/models/evaluate.py", line 133, in <module>
    profiling_data: Dict[str, Any],
                              ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?
- python code/scripts/run_pipeline.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi/code/scripts/run_pipeline.py", line 10, in <module>
    from src.models.evaluate import main as evaluate_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi/code/src/models/evaluate.py", line 133, in <module>
    profiling_data: Dict[str, Any],
                              ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?

## Declared deliverables still missing

- data/baseline_results.csv
- data/permutation_results.csv
- data/profiling_logs.json
- data/sensitivity_analysis.csv
- data/sensitivity_matrix_full.csv
- data/sensitivity_sweep_raw.csv
- data/timing_profile.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/evaluate.py` — NOT invoked by the run-book
    - `code/tests/integration/test_us1_pipeline.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t032_quickstart_validation.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/permutation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_t032_quickstart_validation.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/permutation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/profiling_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/profiles.py` — NOT invoked by the run-book
    - `code/tests/unit/test_reports.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t032_quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t024_timing.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
    - `code/scripts/generate_timing_profile.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/profiling_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/evaluate.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t032_quickstart_validation.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/sensitivity_matrix_full.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/evaluate.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t032_quickstart_validation.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/sensitivity_matrix_full.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/sensitivity_sweep_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/metrics.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t032_quickstart_validation.py` — NOT invoked by the run-book
    - `code/scripts/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
    - `code/scripts/generate_sensitivity_matrix.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/sensitivity_sweep_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/timing_profile.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/evaluate.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t032_quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t024_timing.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
    - `code/scripts/generate_timing_profile.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/timing_profile.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
