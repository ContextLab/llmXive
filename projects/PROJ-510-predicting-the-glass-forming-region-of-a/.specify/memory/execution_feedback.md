# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…"""Check for absence of synthetic data indicators."""         d…”
- code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…eturn False, f"Potential synthetic data indicators found: {synth…”
- code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…se, f"Error checking for synthetic data: {e}"      def _check_sc…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/ingestion.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…"""Check for absence of synthetic data indicators."""         d…”; code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…eturn False, f"Potential synthetic data indicators found: {synth…”; code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…se, f"Error checking for synthetic data: {e}"      def _check_sc…”; 4 command(s) failed: python code/ingestion.py (rc=1); python code/features.py (rc=1); python code/train.py (rc=1); 17 declared deliverable(s) absent: data/logs/data_source_audit.json; data/logs/data_validation_status.json; data/logs/schema_validation_status.json

## Failing / missing run-book commands

- python code/ingestion.py -> rc=1
    unner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1166, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'matsci/glass-forming-ability' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 260, in <module>
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 214, in run_ingestion
    df = load_glass_data()
         ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 100, in load_glass_data
    with open(FETCH_ERROR_LOG, 'w') as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/logs/fetch_error.log'
- python code/features.py -> rc=1
    2026-09-22 09:45:24,731 - features - INFO - Starting feature engineering pipeline

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py", line 246, in <module>
    run_features()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py", line 209, in run_features
    raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion.py first.")
FileNotFoundError: Input file not found: data/processed/processed_alloys_raw.csv. Run ingestion.py first.
- python code/train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py", line 13, in <module>
    from sklearn.ensemble import RandomForestRegressor, DummyRegressor
ImportError: cannot import name 'DummyRegressor' from 'sklearn.ensemble' (/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/.venv/lib/python3.11/site-packages/sklearn/ensemble/__init__.py)
- python code/analyze.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py", line 32, in <module>
    def check_collinearity(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
                                                           ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

## Declared deliverables still missing

- data/logs/data_source_audit.json
- data/logs/data_validation_status.json
- data/logs/schema_validation_status.json
- data/logs/training_set_validation.json
- data/models/collinearity_decision.json
- data/models/cv_folds_indices.json
- data/models/cv_metrics.json
- data/models/feature_importance.json
- data/models/initial_model_metrics.json
- data/models/null_model_cv_scores.json
- data/models/null_model_predictions.npy
- data/models/null_model_rmse.json
- data/models/sc002_status.json
- data/models/sensitivity_status.json
- data/models/statistical_comparison.json
- data/processed/processed_alloys.csv
- data/processed/processed_alloys_raw.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/data_source_audit.json` is declared but was NOT written. Scripts referencing it:
    - `code/constitutional_compliance_audit.py` — NOT invoked by the run-book
    - `code/audit_data_source.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/data_source_audit.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/logs/data_validation_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — IS a run-book command
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/data_validation_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/logs/schema_validation_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/features.py` — IS a run-book command
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/schema_validation_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/logs/training_set_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/training_set_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/collinearity_decision.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/t029b_fallback.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/collinearity_decision.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/cv_folds_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/constitutional_compliance_audit.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/cv_folds_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/cv_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
    - `code/constitutional_compliance_audit.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/statistical_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/cv_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/feature_importance.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/t029b_fallback.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/feature_importance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/initial_model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/t029b_fallback.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/initial_model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/null_model_cv_scores.json` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
    - `code/constitutional_compliance_audit.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/statistical_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/null_model_cv_scores.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/null_model_predictions.npy` is declared but was NOT written. Scripts referencing it:
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/null_model_predictions.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/null_model_rmse.json` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/null_model_rmse.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/sc002_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
    - `code/t024c_gate.py` — NOT invoked by the run-book
    - `code/check_sc002.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/sc002_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/sensitivity_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/t031_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/check_sc003.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/sensitivity_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/statistical_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
    - `code/constitutional_compliance_audit.py` — NOT invoked by the run-book
    - `code/t024c_gate.py` — NOT invoked by the run-book
    - `code/check_sc002.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/statistical_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/statistical_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/processed_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
    - `code/analyze.py` — IS a run-book command
    - `code/constitutional_compliance_audit.py` — NOT invoked by the run-book
    - `code/validate_data_availability.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
    - `code/features.py` — IS a run-book command
    - `code/validate_data.py` — NOT invoked by the run-book
    - `code/t031_sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/processed_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/processed_alloys_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — IS a run-book command
    - `code/features.py` — IS a run-book command
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/processed_alloys_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/processed_alloys.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/train.py`, `code/analyze.py`, `code/constitutional_compliance_audit.py`, `code/features.py`, `code/t031_sensitivity_analysis.py`, `code/audit_data_source.py`, `code/t029b_fallback.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/processed_alloys.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/train.py`, `code/analyze.py`, `code/constitutional_compliance_audit.py`, `code/validate_data_availability.py`, `code/features.py`, `code/validate_data.py`, `code/t031_sensitivity_analysis.py`, `code/validate_schemas.py`, `code/audit_data_source.py`, `code/t029b_fallback.py`.

### `data/processed/processed_alloys_raw.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/ingestion.py`, `code/features.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/processed_alloys_raw.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/ingestion.py`, `code/features.py`, `code/validate_schemas.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/train.py`, `code/analyze.py`, `code/constitutional_compliance_audit.py`, `code/t031_sensitivity_analysis.py`, `code/t029b_fallback.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/train.py`, `code/analyze.py`, `code/constitutional_compliance_audit.py`, `code/t031_sensitivity_analysis.py`, `code/validate_schemas.py`, `code/t029b_fallback.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/train.py`, `code/analyze.py`, `code/constitutional_compliance_audit.py`, `code/features.py`, `code/t031_sensitivity_analysis.py`, `code/audit_data_source.py`, `code/t029b_fallback.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/train.py`, `code/analyze.py`, `code/constitutional_compliance_audit.py`, `code/validate_data_availability.py`, `code/features.py`, `code/validate_data.py`, `code/t031_sensitivity_analysis.py`, `code/validate_schemas.py`, `code/audit_data_source.py`, `code/t029b_fallback.py`.
