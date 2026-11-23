# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Adsorption…”
- code/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…eters.  Generates N=5000 synthetic records linking molecular descri…”
- code/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic adsorption dataset.…”
- code/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…:         DataFrame with synthetic adsorption data.     """     # Molecular…”
- code/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…n df  def main():     """Generate and save synthetic data to disk."""     pri…”
- code/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…f"Generating {N_SAMPLES} synthetic samples...")     df = generate_s…”
- code/data/validate_schema.py: synthetic/fake INPUT data not authorized by the spec — “…schema validation on the generated synthetic data."""     schema_path…”
- code/data/verified_source_enforcer.py: synthetic/fake INPUT data not authorized by the spec — “…ation mode (Phase 3). If synthetic data is detected during a Pha…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 21 fabricated/simulated-result signal(s) — results are not real measurements: code/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Adsorption…”; code/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…eters.  Generates N=5000 synthetic records linking molecular descri…”; code/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic adsorption dataset.…”; 3 command(s) failed: python code/main.py --data-dir data/raw --task curate_data (rc=1); python code/main.py --data-dir data/processed --task train_model --target langmuir_capacity (rc=1); python code/main.py --data-dir data/processed --model trained_models/best_model.pkl --task shap_analysis (rc=1); 12 declared deliverable(s) absent: data/benchmarks/runtime_log.json; data/processed/imputed_dataset.parquet; data/raw/merged_dataset.parquet

## Failing / missing run-book commands

- python code/main.py --data-dir data/raw --task curate_data -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/main.py", line 9, in <module>
    from data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/data/download.py", line 6, in <module>
    import pyarrow as pa
ModuleNotFoundError: No module named 'pyarrow'
- python code/main.py --data-dir data/processed --task train_model --target langmuir_capacity -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/main.py", line 9, in <module>
    from data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/data/download.py", line 6, in <module>
    import pyarrow as pa
ModuleNotFoundError: No module named 'pyarrow'
- python code/main.py --data-dir data/processed --model trained_models/best_model.pkl --task shap_analysis -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/main.py", line 9, in <module>
    from data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/data/download.py", line 6, in <module>
    import pyarrow as pa
ModuleNotFoundError: No module named 'pyarrow'

## Declared deliverables still missing

- data/benchmarks/runtime_log.json
- data/processed/imputed_dataset.parquet
- data/raw/merged_dataset.parquet
- data/results/null_model_fold_rmses.json
- data/results/reduced_model_metrics.json
- data/results/shap_summary.json
- data/validation/exclusion_log.json
- data/validation/missing_descriptors_kinetic.json
- data/validation/missing_descriptors_lj.json
- data/validation/missing_descriptors_quadrupole.json
- data/validation/missing_descriptors_report.json
- data/validation/null_model_comparison.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/benchmarks/runtime_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/utils/benchmark.py` — NOT invoked by the run-book
    - `code/utils/profiler.py` — NOT invoked by the run-book
    - `code/utils/runtime_logger.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/benchmarks/runtime_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/imputed_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/imputation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/imputed_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/merged_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/merge.py` — NOT invoked by the run-book
    - `code/data/imputation.py` — NOT invoked by the run-book
    - `code/data/verify_real.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/merged_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/null_model_fold_rmses.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/null_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/null_model_fold_rmses.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/reduced_model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/retrain_top3.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/reduced_model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/shap_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/benchmark.py` — NOT invoked by the run-book
    - `code/interpret/shap_stability.py` — NOT invoked by the run-book
    - `code/interpret/shap_analysis.py` — NOT invoked by the run-book
    - `code/models/retrain_top3.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/shap_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptors.py` — NOT invoked by the run-book
    - `code/data/imputation.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/analysis/cluster_permutation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/missing_descriptors_kinetic.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/missing_descriptors_kinetic.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/missing_descriptors_lj.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/missing_descriptors_lj.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/missing_descriptors_quadrupole.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/missing_descriptors_quadrupole.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/missing_descriptors_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/missing_descriptors_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/null_model_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/null_comparison.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/null_model_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
