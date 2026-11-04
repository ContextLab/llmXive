# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/validation/produce_smoke_results.py: self-declared fabricated metric — “…ated dataset. If the required simulated measurement file does not exist, it is ge…”
- code/validation/produce_smoke_results.py: self-declared fabricated metric — “…""     Create a deterministic simulated measurement_records CSV with baseline and…”
- code/validation/produce_smoke_results.py: self-declared fabricated metric — “…lse)     log.info(f"Generated simulated measurement file at {csv_path}")   def lo…”
- code/validation/produce_smoke_results.py: self-declared fabricated metric — “…: Path):     """     Load the simulated measurement records CSV and organise the…”
- code/validation/produce_smoke_results.py: self-declared fabricated metric — “….is_file():         log.info("Simulated measurement file not found – generating o…”
- code/validation/produce_smoke_results.py: self-declared fabricated metric — “…eNotFoundError(             f"Simulated measurement file not found at {raw_measur…”
- code/validation/produce_smoke_results.py: self-declared fabricated metric — “…)      log.info(f"Loading simulated measurements from {raw_measurements_path}…”
- code/validation/validate_schema.py: self-declared fabricated metric — “…int(f"Generated deterministic simulated measurement file at {csv_path}")  def _bu…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 70 fabricated/simulated-result signal(s) — results are not real measurements: code/validation/produce_smoke_results.py: self-declared fabricated metric — “…ated dataset. If the required simulated measurement file does not exist, it is ge…”; code/validation/produce_smoke_results.py: self-declared fabricated metric — “…""     Create a deterministic simulated measurement_records CSV with baseline and…”; code/validation/produce_smoke_results.py: self-declared fabricated metric — “…lse)     log.info(f"Generated simulated measurement file at {csv_path}")   def lo…”; 1 command(s) failed: python -m pytest -v (rc=2); 8 declared deliverable(s) absent: data/processed/aggregated_compliance.csv; data/processed/change_scores.csv; data/processed/compliance_flags.json

## Failing / missing run-book commands

- python -m pytest -v -> rc=2
e/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR code/tests/test_run_all.py
ERROR code/tests/test_t001_setup.py
ERROR tests/integration/test_layout.py
ERROR tests/integration/test_questionnaire.py - json.decoder.JSONDecodeError:...
ERROR tests/test_linting_config.py
ERROR tests/unit/test_bootstrap_ci.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_edge_cases.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 23 warnings, 8 errors in 2.39s ========================



## Declared deliverables still missing

- data/processed/aggregated_compliance.csv
- data/processed/change_scores.csv
- data/processed/compliance_flags.json
- data/processed/descriptive_baseline.csv
- data/raw/measurement_records_sim.csv
- data/raw/participants.csv
- data/raw/participants_simulated.csv
- data/raw/questionnaire_responses.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aggregated_compliance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/compliance/compute_compliance.py` — NOT invoked by the run-book
    - `code/compliance/tests/test_compute_compliance.py` — NOT invoked by the run-book
    - `code/pipeline/merge_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aggregated_compliance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/change_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/change_scores.py` — NOT invoked by the run-book
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/statistical_summary.py` — NOT invoked by the run-book
    - `code/pipeline/merge_data.py` — NOT invoked by the run-book
    - `code/pipeline/validate_quickstart.py` — NOT invoked by the run-book
    - `code/viz/generate_plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/change_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/compliance_flags.json` is declared but was NOT written. Scripts referencing it:
    - `code/compliance/compute_compliance.py` — NOT invoked by the run-book
    - `code/compliance/tests/test_compute_compliance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/compliance_flags.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptive_baseline.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline/handle_dropouts.py` — NOT invoked by the run-book
    - `code/pipeline/merge_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptive_baseline.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/measurement_records_sim.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_simulated_schema.py` — NOT invoked by the run-book
    - `code/validation/produce_smoke_results.py` — NOT invoked by the run-book
    - `code/validation/simulate_study.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/measurement_records_sim.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/participants.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/change_scores.py` — NOT invoked by the run-book
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/power_simulation.py` — NOT invoked by the run-book
    - `code/compliance/flag_non_compliant.py` — NOT invoked by the run-book
    - `code/compliance/log_extreme_cases.py` — NOT invoked by the run-book
    - `code/compliance/tests/test_compute_compliance.py` — NOT invoked by the run-book
    - `code/pipeline/aggregate_compliance.py` — NOT invoked by the run-book
    - `code/pipeline/collect_baseline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/participants.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/participants_simulated.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validation/generate_checksums.py` — NOT invoked by the run-book
    - `code/validation/simulate_study.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/participants_simulated.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/questionnaire_responses.csv` is declared but was NOT written. Scripts referencing it:
    - `code/web/questionnaires/pss_panas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/questionnaire_responses.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
