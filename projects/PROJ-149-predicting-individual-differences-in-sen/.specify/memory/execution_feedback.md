# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/generate_report.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/generate_report.py; 7 command(s) failed: python code/01_download_data.py (rc=1); python code/01_download_data.py --check-feasibility (rc=1); python code/02_preprocess_eeg.py (rc=1); 19 declared deliverable(s) absent: data/interim/behavioral_exclusion_log.csv; data/interim/behavioral_metrics.csv; data/interim/correlations_raw.csv

## Failing / missing run-book commands

- python code/01_download_data.py -> rc=1
    Data directory missing or empty. Downloading...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 231, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 188, in main
    download_dataset()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 48, in download_dataset
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'
- python code/01_download_data.py --check-feasibility -> rc=1
    Data directory missing or empty. Downloading...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 231, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 188, in main
    download_dataset()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 48, in download_dataset
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'
- python code/02_preprocess_eeg.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/02_preprocess_eeg.py", line 23, in <module>
    from config import get_path, ensure_dirs, get_filter_params, get_ica_params, get_exclusion_params
ImportError: cannot import name 'get_filter_params' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py)
- python code/03_extract_features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/03_extract_features.py", line 21, in <module>
    from config import (
ImportError: cannot import name 'get_epsilon' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py)
- python code/04_modeling.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/04_modeling.py", line 25, in <module>
    from config import get_path, ensure_dirs, get_cv_folds, get_seed
ImportError: cannot import name 'get_cv_folds' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/04_modeling.py", line 30, in <module>
    from config import get_path, ensure_dirs, get_cv_folds, get_seed
ImportError: cannot import name 'get_cv_folds' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py)
- python code/05_robustness_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/05_robustness_analysis.py", line 30, in <module>
    from config import get_path, get_band_freqs, get_all_band_names, get_filter_params, ensure_dirs, get_seed
ImportError: cannot import name 'get_band_freqs' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py)
- python code/06_sensitivity_analysis.py -> rc=1
    Loading correlations data...
Error: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/data/processed/correlations.csv. Please ensure T025 (generate_final_correlation_outputs) has completed successfully.
- python code/generate_report.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/generate_report.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/interim/behavioral_exclusion_log.csv
- data/interim/behavioral_metrics.csv
- data/interim/correlations_raw.csv
- data/interim/data_source_manifest.json
- data/interim/exclusion_log.csv
- data/interim/feasibility_exclusion_log.csv
- data/interim/joined_metadata.csv
- data/interim/nonlinear_model_results.json
- data/interim/permutation_null_distribution.npy
- data/interim/poly_features.csv
- data/interim/split_indices.json
- data/processed/correlations_corrected.csv
- data/processed/features.csv
- data/processed/model_results.json
- data/processed/non_linear_comparison.json
- data/processed/permutation_results.json
- data/processed/robustness_model_results.json
- data/processed/sensitivity_plot.png
- data/processed/sensitivity_report.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_dirs` — defined in `code/config.py`; called 25 way(s):

- code/03_extract_features.py: ensure_dirs(output_path)
- code/07_generate_report.py: ensure_dirs(output_path.parent)
- code/04_modeling_lasso.py: output_dir = ensure_dirs("data/processed")
- code/00_feasibility_check_report.py: ensure_dirs(output_path)
- code/09_robustness_modeling.py: ensure_dirs(output_dir)
- code/12_nonlinear_analysis.py: ensure_dirs(output)
- code/08c_compare_models.py: ensure_dirs(output_path)
- code/12_feasibility_check.py: - ensure_dirs()
- code/12_feasibility_check.py: - ensure_dirs(path)
- code/12_feasibility_check.py: - ensure_dirs([path])
- code/12_feasibility_check.py: - ensure_dirs(path, mode)
- code/01_download_data.py: ensure_dirs(dest_dir)
- code/01_download_data.py: ensure_dirs(data_raw_dir)
- code/01_download_data.py: ensure_dirs(manifest_dir)
- code/code_03_extract_features.py: ensure_dirs(output_path)
- code/05_robustness_analysis.py: ensure_dirs([proc_data_dir])
- code/06_validate_features.py: ensure_dirs(Path(log_path).parent)
- code/config.py: - ensure_dirs() -> does nothing (or creates root?)
- code/config.py: - ensure_dirs("path") -> creates PROJECT_ROOT / path
- code/config.py: - ensure_dirs(Path_obj) -> creates Path_obj
- code/config.py: - ensure_dirs(["path1", "path2"]) -> creates all
- code/config.py: - ensure_dirs(path_obj, another_obj) -> creates all
- code/config.py: # Some callers assign the result: output_dir = ensure_dirs(...)
- code/04_extract_features.py: ensure_dirs(output_dir)
- code/15_verify_success_criteria.py: ensure_dirs(output_path)

Make `ensure_dirs` in `code/config.py` accept ALL of the above.

### `get_path` — defined in `code/config.py`; called 25 way(s):

- code/03_extract_features.py: exclusion_log_path = get_path("interim", "exclusion_log.csv")
- code/03_extract_features.py: b_path = get_path("interim", "behavioral_metrics.csv")
- code/03_extract_features.py: eeg_dir = get_path("interim", "cleaned_eeg_final")
- code/03_extract_features.py: output_path = get_path("processed", "features_clr.csv")
- code/07_generate_report.py: model_results_path = get_path(base_dir, "data/processed/model_results.json")
- code/07_generate_report.py: correlations_path = get_path(base_dir, "data/processed/correlations.csv")
- code/07_generate_report.py: robustness_path = get_path(base_dir, "data/processed/robustness_report.csv")
- code/07_generate_report.py: sensitivity_plot_path = get_path(base_dir, "data/processed/sensitivity_plot.png")
- code/07_generate_report.py: verification_path = get_path(base_dir, "data/processed/verification_log.json")
- code/07_generate_report.py: metadata_path = get_path(base_dir, "data/interim/joined_metadata.csv")
- code/07_generate_report.py: output_path = get_path(base_dir, "data/processed/final_report.md")
- code/04_modeling_lasso.py: path = get_path("data/processed/features.csv")
- code/04_modeling_lasso.py: path = get_path("data/interim/split_indices.json")
- code/07_permutation_test.py: features_path = get_path('processed', 'features_clr.csv')
- code/07_permutation_test.py: observed_results_path = get_path('processed', 'model_results.json')
- code/07_permutation_test.py: output_json_path = get_path('processed', 'permutation_results.json')
- code/07_permutation_test.py: output_npy_path = get_path('interim', 'permutation_null_distribution.npy')
- code/00_feasibility_check_report.py: status_path = get_path('interim', 'join_status.json')
- code/00_feasibility_check_report.py: output_path = get_path('processed', 'feasibility_report.md')
- code/09_robustness_modeling.py: input_path = args.input or get_path('data/processed/robustness_features_2s.csv')
- code/09_robustness_modeling.py: output_path = args.output or get_path('data/processed/robustness_model_results.json')
- code/08c_compare_models.py: input_path = get_path("interim", "nonlinear_model_results.json")
- code/08c_compare_models.py: output_path = get_path("processed", "non_linear_comparison.json")
- code/12_feasibility_check.py: - get_path("data/processed/file.json")
- code/12_feasibility_check.py: - get_path("processed", "file.json")

Make `get_path` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/behavioral_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/03_behavioral_parsing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/behavioral_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_extract_features.py` — IS a run-book command
    - `code/12_feasibility_check.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/04_extract_features.py` — NOT invoked by the run-book
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
    - `code/05_compute_relative_power.py` — NOT invoked by the run-book
    - `code/09_robustness_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/correlations_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
    - `code/10_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/06_correlations.py` — NOT invoked by the run-book
    - `code/09_apply_bonferroni.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/correlations_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/data_source_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_download_data.py` — IS a run-book command
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/data_source_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_extract_features.py` — IS a run-book command
    - `code/04_extract_features.py` — NOT invoked by the run-book
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
    - `code/09_robustness_features.py` — NOT invoked by the run-book
    - `code/05_robustness_preprocess.py` — NOT invoked by the run-book
    - `code/02_preprocess_eeg.py` — IS a run-book command
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/feasibility_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/feasibility_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/joined_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — NOT invoked by the run-book
    - `code/12_feasibility_check.py` — NOT invoked by the run-book
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/03_behavioral_parsing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/joined_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/nonlinear_model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/08c_compare_models.py` — NOT invoked by the run-book
    - `code/08b_fit_nonlinear_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/nonlinear_model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/permutation_null_distribution.npy` is declared but was NOT written. Scripts referencing it:
    - `code/07_permutation_test.py` — NOT invoked by the run-book
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/permutation_null_distribution.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/poly_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/08b_fit_nonlinear_model.py` — NOT invoked by the run-book
    - `code/08a_prepare_polynomial_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/poly_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/04_modeling.py` — IS a run-book command
    - `code/05_modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlations_corrected.csv` is declared but was NOT written. Scripts referencing it:
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/09_apply_bonferroni.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlations_corrected.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_extract_features.py` — IS a run-book command
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/07_permutation_test.py` — NOT invoked by the run-book
    - `code/09_robustness_modeling.py` — NOT invoked by the run-book
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/12_feasibility_check.py` — NOT invoked by the run-book
    - `code/code_03_extract_features.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — NOT invoked by the run-book
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/07_permutation_test.py` — NOT invoked by the run-book
    - `code/09_robustness_modeling.py` — NOT invoked by the run-book
    - `code/08c_compare_models.py` — NOT invoked by the run-book
    - `code/12_feasibility_check.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/non_linear_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/08c_compare_models.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/non_linear_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/permutation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/07_permutation_test.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/permutation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/09_robustness_modeling.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — NOT invoked by the run-book
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/14_generate_robustness_and_sensitivity_outputs.py` — NOT invoked by the run-book
    - `code/10_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/10_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/data/processed/correlations.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/07_generate_report.py`, `code/15_verify_success_criteria.py`, `code/08_correlation_analysis.py`, `code/13_generate_final_correlation_outputs.py`, `code/06_validate_model_results.py`, `code/06_sensitivity_sweep.py`, `code/06_sensitivity_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/data/processed/correlations.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/07_generate_report.py`, `code/15_verify_success_criteria.py`, `code/08_correlation_analysis.py`, `code/13_generate_final_correlation_outputs.py`, `code/06_validate_model_results.py`, `code/06_sensitivity_sweep.py`, `code/06_sensitivity_analysis.py`.
