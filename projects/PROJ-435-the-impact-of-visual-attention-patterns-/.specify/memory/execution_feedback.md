# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/05_synthetic_data_generator.py: metric `crt_score` assigned from an RNG draw (line 85)
- code/03_data_merge.py: synthetic/fake INPUT data not authorized by the spec — “…ask T023: Merge Gaze and Synthetic Data Streams with Outlier Cap…”
- code/03_data_merge.py: synthetic/fake INPUT data not authorized by the spec — “…ata (from T018) with the synthetic raw data (from T022) on participa…”
- code/03_data_merge.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """Load synthetic raw data from T022."""     if not…”
- code/03_data_merge.py: synthetic/fake INPUT data not authorized by the spec — “…(             f"Required synthetic data file not found: {synthet…”
- code/03_data_merge.py: synthetic/fake INPUT data not authorized by the spec — “…logging.info(f"Loading synthetic data from {synthetic_path}")…”
- code/03_data_merge.py: synthetic/fake INPUT data not authorized by the spec — “…raise ValueError(f"Synthetic data missing required columns…”
- code/03_data_merge.py: synthetic/fake INPUT data not authorized by the spec — “…e:     """Merge gaze and synthetic data on participant_id and he…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 16 fabricated/simulated-result signal(s) — results are not real measurements: code/05_synthetic_data_generator.py: metric `crt_score` assigned from an RNG draw (line 85); code/03_data_merge.py: synthetic/fake INPUT data not authorized by the spec — “…ask T023: Merge Gaze and Synthetic Data Streams with Outlier Cap…”; code/03_data_merge.py: synthetic/fake INPUT data not authorized by the spec — “…ata (from T018) with the synthetic raw data (from T022) on participa…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/cli/run_pipeline.py --stage preprocess; python code/cli/run_pipeline.py --stage valence; python code/cli/run_pipeline.py --stage analyze; 1 command(s) failed: python -m pytest tests/ (rc=2); 7 declared deliverable(s) absent: data/derived/empirical_outcomes.csv; data/derived/merged_dataset_full.csv; data/derived/preprocessed_gaze.csv

## Failing / missing run-book commands

- python code/cli/run_pipeline.py --stage preprocess -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-435-the-impact-of-visual-attention-patterns-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-435-the-impact-of-visual-attention-patterns-/code/cli/run_pipeline.py': [Errno 2] No such file or directory

- python code/cli/run_pipeline.py --stage valence -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-435-the-impact-of-visual-attention-patterns-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-435-the-impact-of-visual-attention-patterns-/code/cli/run_pipeline.py': [Errno 2] No such file or directory

- python code/cli/run_pipeline.py --stage analyze -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-435-the-impact-of-visual-attention-patterns-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-435-the-impact-of-visual-attention-patterns-/code/cli/run_pipeline.py': [Errno 2] No such file or directory

- python code/cli/run_pipeline.py --stage robustness -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-435-the-impact-of-visual-attention-patterns-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-435-the-impact-of-visual-attention-patterns-/code/cli/run_pipeline.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
med 'code.utils.verify_checksums'
=========================== short test summary info ============================
ERROR tests/contract/test_checksum_verification.py
ERROR tests/integration/test_sensitivity_analysis.py
ERROR tests/unit/test_causal_framing.py
ERROR tests/unit/test_config_loader.py
ERROR tests/unit/test_data_loading.py
ERROR tests/unit/test_data_merge.py
ERROR tests/unit/test_data_quality_report.py
ERROR tests/unit/test_environment_manager.py
ERROR tests/unit/test_logging_infrastructure.py
ERROR tests/unit/test_models.py
ERROR tests/unit/test_performance_optimization.py
ERROR tests/unit/test_regression_analysis.py
ERROR tests/unit/test_robustness_runner.py
ERROR tests/unit/test_robustness_stability_check.py
ERROR tests/unit/test_robustness_sweep.py
ERROR tests/unit/test_roi_mapping.py
ERROR tests/unit/test_runtime_measure.py
ERROR tests/unit/test_stability_check.py
ERROR tests/unit/test_synthetic_data_generator.py
ERROR tests/unit/test_verify_artifacts_checksums.py
ERROR tests/unit/test_verify_checksums.py
!!!!!!!!!!!!!!!!!!! Interrupted: 21 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 21 errors in 3.16s ==============================



## Declared deliverables still missing

- data/derived/empirical_outcomes.csv
- data/derived/merged_dataset_full.csv
- data/derived/preprocessed_gaze.csv
- data/derived/regression_results.csv
- data/derived/robustness_report.csv
- data/derived/valence_scores.csv
- data/raw/eye_tracking_raw.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/empirical_outcomes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_extract_empirical_outcome.py` — NOT invoked by the run-book
    - `code/03_valence_calculation.py` — NOT invoked by the run-book
    - `code/04_data_merge.py` — NOT invoked by the run-book
    - `code/09_performance_optimization.py` — NOT invoked by the run-book
    - `code/robustness_analysis.py` — NOT invoked by the run-book
    - `code/robustness_sweep.py` — NOT invoked by the run-book
    - `code/utils/environment_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/empirical_outcomes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/merged_dataset_full.csv` is declared but was NOT written. Scripts referencing it:
    - `code/049_run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/04_data_merge.py` — NOT invoked by the run-book
    - `code/05_regression_analysis.py` — NOT invoked by the run-book
    - `code/06_generate_regression_results.py` — NOT invoked by the run-book
    - `code/09_performance_optimization.py` — NOT invoked by the run-book
    - `code/robustness_runner.py` — NOT invoked by the run-book
    - `code/robustness_sweep.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/merged_dataset_full.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/preprocessed_gaze.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest_and_preprocess.py` — NOT invoked by the run-book
    - `code/02_data_quality_report.py` — NOT invoked by the run-book
    - `code/02_preprocess_gaze.py` — NOT invoked by the run-book
    - `code/03_data_merge.py` — NOT invoked by the run-book
    - `code/049_run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/04_data_merge.py` — NOT invoked by the run-book
    - `code/09_performance_optimization.py` — NOT invoked by the run-book
    - `code/robustness_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/preprocessed_gaze.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/regression_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/049_run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/05_regression_analysis.py` — NOT invoked by the run-book
    - `code/06_apply_holm_correction.py` — NOT invoked by the run-book
    - `code/06_generate_regression_results.py` — NOT invoked by the run-book
    - `code/07_generate_causal_framing.py` — NOT invoked by the run-book
    - `code/07_verify_interaction_consistency.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/regression_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/robustness_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/07_stability_check.py` — NOT invoked by the run-book
    - `code/robustness_analysis.py` — NOT invoked by the run-book
    - `code/robustness_stability_check.py` — NOT invoked by the run-book
    - `code/robustness_sweep.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/robustness_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/valence_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_valence_calculation.py` — NOT invoked by the run-book
    - `code/04_data_merge.py` — NOT invoked by the run-book
    - `code/09_performance_optimization.py` — NOT invoked by the run-book
    - `code/robustness_analysis.py` — NOT invoked by the run-book
    - `code/robustness_sweep.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/valence_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/eye_tracking_raw.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/01_extract_empirical_outcome.py` — NOT invoked by the run-book
    - `code/02_preprocess_gaze.py` — NOT invoked by the run-book
    - `code/049_run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/09_performance_optimization.py` — NOT invoked by the run-book
    - `code/utils/data_loading.py` — NOT invoked by the run-book
    - `code/utils/environment_manager.py` — NOT invoked by the run-book
    - `code/utils/validate_dataset_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/eye_tracking_raw.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
