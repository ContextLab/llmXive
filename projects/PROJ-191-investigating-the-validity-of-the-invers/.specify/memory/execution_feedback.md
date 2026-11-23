# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/models/physics.py: self-declared fabricated metric — “…data/config # For now, we use placeholder values that would be calibrated M_S…”
- code/data/generate_harmonized_output.py: synthetic/fake INPUT data not authorized by the spec — “…int = 100):     """     Generate synthetic raw data files that mimi…”
- code/injection_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…nt (alpha) injected into simulated data is recovered within the…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/models/physics.py: self-declared fabricated metric — “…data/config # For now, we use placeholder values that would be calibrated M_S…”; code/data/generate_harmonized_output.py: synthetic/fake INPUT data not authorized by the spec — “…int = 100):     """     Generate synthetic raw data files that mimi…”; code/injection_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…nt (alpha) injected into simulated data is recovered within the…”; 4 run-book script(s) missing (plan/impl path mismatch): python main.py --step download_harmonize; python main.py --step infer; python main.py --step robustness; 1 command(s) failed: python -m pytest tests/ (rc=2); 7 declared deliverable(s) absent: data/processed/config.json; data/processed/data_config.json; data/results/bayes_factor.json

## Failing / missing run-book commands

- python main.py --step download_harmonize -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-191-investigating-the-validity-of-the-invers/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-191-investigating-the-validity-of-the-invers/main.py': [Errno 2] No such file or directory

- python main.py --step infer -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-191-investigating-the-validity-of-the-invers/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-191-investigating-the-validity-of-the-invers/main.py': [Errno 2] No such file or directory

- python main.py --step robustness -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-191-investigating-the-validity-of-the-invers/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-191-investigating-the-validity-of-the-invers/main.py': [Errno 2] No such file or directory

- python main.py --all -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-191-investigating-the-validity-of-the-invers/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-191-investigating-the-validity-of-the-invers/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
nit/test_download_run_count.py:16
  /home/runner/work/llmXive/llmXive/projects/PROJ-191-investigating-the-validity-of-the-invers/tests/unit/test_download_run_count.py:16: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_mcmc_diagnostics.py - TypeError: setup_logging()...
ERROR tests/integration/test_pipeline_runner.py
ERROR tests/integration/test_robustness.py
ERROR tests/test_pipeline_integration.py
ERROR tests/unit/test_cross_val.py
ERROR tests/unit/test_directories.py
ERROR tests/unit/test_injection_recovery.py
ERROR tests/unit/test_mcmc_runner.py
ERROR tests/unit/test_nested_sampling.py
ERROR tests/unit/test_sc002_verifier.py
ERROR tests/unit/test_uncertainty.py
!!!!!!!!!!!!!!!!!!! Interrupted: 11 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 1 warning, 11 errors in 1.13s =========================



## Declared deliverables still missing

- data/processed/config.json
- data/processed/data_config.json
- data/results/bayes_factor.json
- data/results/mcmc_chains.npy
- data/results/null_baseline_report.json
- data/results/robustness_metrics.json
- data/results/validity_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/config.json` is declared but was NOT written. Scripts referencing it:
    - `code/agents/sc002_verifier.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/fallback_logic.py` — NOT invoked by the run-book
    - `code/data/generate_harmonized_output.py` — NOT invoked by the run-book
    - `code/data/harmonize.py` — NOT invoked by the run-book
    - `code/data/models.py` — NOT invoked by the run-book
    - `code/data/parsers.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/data_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/inference/mcmc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/data_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/bayes_factor.json` is declared but was NOT written. Scripts referencing it:
    - `code/agents/sc002_verifier.py` — NOT invoked by the run-book
    - `code/inference/nested.py` — NOT invoked by the run-book
    - `code/robustness/cross_val.py` — NOT invoked by the run-book
    - `code/robustness/parallel_runner.py` — NOT invoked by the run-book
    - `code/robustness/uncertainty.py` — NOT invoked by the run-book
    - `code/utils/plotting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/bayes_factor.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/mcmc_chains.npy` is declared but was NOT written. Scripts referencing it:
    - `code/utils/plotting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/mcmc_chains.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/null_baseline_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/agents/sc002_verifier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/null_baseline_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/robustness_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_runner.py` — NOT invoked by the run-book
    - `code/robustness/cross_val.py` — NOT invoked by the run-book
    - `code/robustness/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/robustness_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/validity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/agents/sc002_verifier.py` — NOT invoked by the run-book
    - `code/pipeline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/validity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
