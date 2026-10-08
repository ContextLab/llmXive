# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/generate_report.py; 7 command(s) failed: python code/01_download_data.py (rc=1); python code/01_download_data.py --check-feasibility (rc=1); python code/02_preprocess_eeg.py (rc=1); 24 declared deliverable(s) absent: data/interim/behavioral_exclusion_log.csv; data/interim/behavioral_metrics.csv; data/interim/correlations_raw.csv

## Failing / missing run-book commands

- python code/01_download_data.py -> rc=1
    odule>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 189, in main
    ensure_dirs(output_manifest_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in ensure_dirs
    _process(paths)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 66, in _process
    path_obj = pathlib.Path(p) if not isinstance(p, pathlib.Path) else p
               ^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/pathlib.py", line 871, in __new__
    self = cls._from_parts(args)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/pathlib.py", line 509, in _from_parts
    drv, root, parts = self._parse_args(args)
                       ^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/pathlib.py", line 493, in _parse_args
    a = os.fspath(a)
        ^^^^^^^^^^^^
TypeError: expected str, bytes or os.PathLike object, not tuple
- python code/01_download_data.py --check-feasibility -> rc=1
    odule>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 189, in main
    ensure_dirs(output_manifest_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in ensure_dirs
    _process(paths)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 66, in _process
    path_obj = pathlib.Path(p) if not isinstance(p, pathlib.Path) else p
               ^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/pathlib.py", line 871, in __new__
    self = cls._from_parts(args)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/pathlib.py", line 509, in _from_parts
    drv, root, parts = self._parse_args(args)
                       ^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/pathlib.py", line 493, in _parse_args
    a = os.fspath(a)
        ^^^^^^^^^^^^
TypeError: expected str, bytes or os.PathLike object, not tuple
- python code/02_preprocess_eeg.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/02_preprocess_eeg.py", line 24, in <module>
    from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica
ImportError: cannot import name 'reject_channels_by_variance' from 'utils.eeg_helpers' (/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/utils/eeg_helpers.py)
- python code/03_extract_features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/03_extract_features.py", line 21, in <module>
    from config import (
ImportError: cannot import name 'get_window_seconds' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py)
- python code/04_modeling.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/04_modeling.py", line 26, in <module>
    from utils.stats_helpers import bonferroni_correct
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/utils/stats_helpers.py", line 204
    n_predictors: int = 6
    ^^^^^^^^^^^^^^^^^
SyntaxError: duplicate argument 'n_predictors' in function definition
- python code/05_robustness_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/05_robustness_analysis.py", line 31, in <module>
    from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance
ImportError: cannot import name 'reject_channels_by_variance' from 'utils.eeg_helpers' (/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/utils/eeg_helpers.py)
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
- data/interim/feasibility_exclusion_log.csv
- data/interim/feasibility_filtered.csv
- data/interim/final_exclusion_log.csv
- data/interim/final_participant_list.csv
- data/interim/halt_signal.json
- data/interim/joined_metadata.csv
- data/interim/nonlinear_model_results.json
- data/interim/permutation_null_distribution.npy
- data/interim/poly_features.csv
- data/interim/psd_spectra.npy
- data/interim/rt_data_manifest.json
- data/processed/correlations_corrected.csv
- data/processed/features.csv
- data/processed/model_results.json
- data/processed/non_linear_comparison.json
- data/processed/permutation_results.json
- data/processed/robustness_features_2s.csv
- data/processed/robustness_model_results.json
- data/processed/sensitivity_plot.png
- data/processed/sensitivity_report.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_dirs` — defined in `code/08b_fit_nonlinear_model.py`; called 25 way(s):

- code/code_03_extract_features.py: ensure_dirs(output_path)
- code/09_robustness_modeling.py: ensure_dirs(output_dir)
- code/04_modeling.py: ensure_dirs(Path(output_dir))
- code/04_modeling.py: ensure_dirs(Path(os.path.dirname(split_indices_path)))
- code/04_extract_features.py: ensure_dirs(output_dir)
- code/09_power_analysis.py: ensure_dirs(output_path)
- code/04c_relative_power.py: ensure_dirs(output_path.parent)
- code/01_download_rt_data.py: ensure_dirs(rt_data_dir)
- code/01_download_rt_data.py: ensure_dirs(manifest_path.parent)
- code/11_posthoc_power_analysis.py: ensure_dirs(output_path)
- code/00_feasibility_filter_segments.py: ensure_dirs(output_path)
- code/05_robustness_features.py: ensure_dirs(output_dir)
- code/11_generate_report.py: ensure_dirs(Path(output_path).parent)
- code/08b_fit_nonlinear_model.py: ensure_dirs(output_path)
- code/download_data.py: ensure_dirs(RAW_DATA_DIR)
- code/download_data.py: ensure_dirs(INTERIM_DIR)
- code/11c_write_report.py: ensure_dirs(output_path)
- code/08c_compare_models.py: ensure_dirs(Path(output_path).parent)
- code/05_robustness_analysis.py: ensure_dirs([proc_data_dir])
- code/05_robustness_preprocess.py: ensure_dirs(output_dir)
- code/05_robustness_preprocess.py: ensure_dirs(exclusion_log_path)
- code/05_robustness_preprocess.py: ensure_dirs(os.path.dirname(os.path.dirname(robustness_output_dir)))
- code/12_nonlinear_analysis.py: ensure_dirs(output)
- code/14_generate_robustness_and_sensitivity_outputs.py: ensure_dirs([args.robustness_output, args.sensitivity_output])
- code/15_verify_success_criteria.py: ensure_dirs(output_path)

Make `ensure_dirs` in `code/08b_fit_nonlinear_model.py` accept ALL of the above.

### `get_path` — defined in `code/08b_fit_nonlinear_model.py`; called 25 way(s):

- code/code_03_extract_features.py: input_path = get_path(INPUT_DIR)
- code/code_03_extract_features.py: input_path = get_path(args.input_dir)
- code/code_03_extract_features.py: output_path = get_path(args.output_file)
- code/09_robustness_modeling.py: input_path = args.input or get_path('data/processed/robustness_features_2s.csv')
- code/09_robustness_modeling.py: output_path = args.output or get_path('data/processed/robustness_model_results.json')
- code/04_modeling.py: input_path = args.input or get_path("features_clr")
- code/04_modeling.py: output_path = args.output or get_path("model_results")
- code/04_modeling.py: split_indices_path = args.splits or get_path("split_indices")
- code/04_extract_features.py: eeg_files = glob.glob(os.path.join(get_path("interim", "preprocessed_eeg"), "*.fif"))
- code/04_extract_features.py: alt_path = os.path.join(get_path("interim"), "behavioral_metrics.csv")
- code/04_extract_features.py: preprocessed_dir = args.preprocessed_dir or get_path("interim", "ica_cleaned_eeg")
- code/04_extract_features.py: behavioral_path = args.behavioral_path or get_path("interim", "behavioral_metrics.csv")
- code/04_extract_features.py: exclusion_log_path = args.exclusion_log or get_path("interim", "exclusion_log.csv")
- code/04_extract_features.py: output_dir = args.output_dir or get_path("processed")
- code/09_power_analysis.py: input_path = get_path('processed', 'model_results.json')
- code/09_power_analysis.py: features_path = get_path('processed', 'features.csv')
- code/09_power_analysis.py: split_path = get_path('interim', 'split_indices_primary.json')
- code/09_power_analysis.py: output_path = args.output or get_path('processed', 'model_results.json')
- code/04c_relative_power.py: default=str(get_path("interim", "band_powers.csv")),
- code/04c_relative_power.py: default=str(get_path("interim", "behavioral_metrics.csv")),
- code/04c_relative_power.py: default=str(get_path("interim", "joined_metadata.csv")),
- code/04c_relative_power.py: default=str(get_path("processed", "features.csv")),
- code/01_download_rt_data.py: rt_data_dir = get_path(DATA_RAW_DIR)
- code/01_download_rt_data.py: manifest_path = get_path(INTERIM_DIR) / "rt_data_manifest.json"
- code/11_posthoc_power_analysis.py: results_path = get_path("processed", "model_results.json")

Make `get_path` in `code/08b_fit_nonlinear_model.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/behavioral_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
    - `code/03_behavioral_parsing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/behavioral_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_extract_features.py` — NOT invoked by the run-book
    - `code/04c_relative_power.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/12_feasibility_check.py` — NOT invoked by the run-book
    - `code/05_compute_relative_power.py` — NOT invoked by the run-book
    - `code/09_robustness_features.py` — NOT invoked by the run-book
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
    - `code/03_behavioral_parsing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/correlations_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/10_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/09_apply_bonferroni.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
    - `code/06_correlations.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/correlations_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/data_source_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_data.py` — NOT invoked by the run-book
    - `code/01_download_data.py` — IS a run-book command
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/00_feasibility_join.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/data_source_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/feasibility_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_filter_segments.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/00_feasibility_join.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/feasibility_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/feasibility_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_filter_segments.py` — NOT invoked by the run-book
    - `code/00_feasibility_check_channels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/feasibility_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/final_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_channels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/final_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/final_participant_list.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_channels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/final_participant_list.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/halt_signal.json` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_channels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/halt_signal.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/joined_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04c_relative_power.py` — NOT invoked by the run-book
    - `code/00_feasibility_filter_segments.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/12_feasibility_check.py` — NOT invoked by the run-book
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/00_feasibility_join.py` — NOT invoked by the run-book
    - `code/04_extract_psd.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/joined_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/nonlinear_model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/08b_fit_nonlinear_model.py` — NOT invoked by the run-book
    - `code/08c_compare_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/nonlinear_model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/permutation_null_distribution.npy` is declared but was NOT written. Scripts referencing it:
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
    - `code/07_permutation_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/permutation_null_distribution.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/poly_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/08b_fit_nonlinear_model.py` — NOT invoked by the run-book
    - `code/08a_prepare_polynomial_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/poly_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/psd_spectra.npy` is declared but was NOT written. Scripts referencing it:
    - `code/04_extract_psd.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/psd_spectra.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/rt_data_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_download_rt_data.py` — NOT invoked by the run-book
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/00_feasibility_join.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/rt_data_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlations_corrected.csv` is declared but was NOT written. Scripts referencing it:
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/09_apply_bonferroni.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlations_corrected.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/code_03_extract_features.py` — NOT invoked by the run-book
    - `code/09_robustness_modeling.py` — NOT invoked by the run-book
    - `code/04_modeling.py` — IS a run-book command
    - `code/04_extract_features.py` — NOT invoked by the run-book
    - `code/09_power_analysis.py` — NOT invoked by the run-book
    - `code/04c_relative_power.py` — NOT invoked by the run-book
    - `code/11_posthoc_power_analysis.py` — NOT invoked by the run-book
    - `code/05_robustness_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/09_robustness_modeling.py` — NOT invoked by the run-book
    - `code/04_modeling.py` — IS a run-book command
    - `code/09_power_analysis.py` — NOT invoked by the run-book
    - `code/11_posthoc_power_analysis.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/08b_fit_nonlinear_model.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/08c_compare_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/non_linear_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/08c_compare_models.py` — NOT invoked by the run-book
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/non_linear_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/permutation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
    - `code/07_permutation_test.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/permutation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_features_2s.csv` is declared but was NOT written. Scripts referencing it:
    - `code/09_robustness_modeling.py` — NOT invoked by the run-book
    - `code/09_robustness_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_features_2s.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/09_robustness_modeling.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/10_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/14_generate_robustness_and_sensitivity_outputs.py` — NOT invoked by the run-book
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/10_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/data/processed/correlations.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/15_verify_success_criteria.py`, `code/06_sensitivity_analysis.py`, `code/13_generate_final_correlation_outputs.py`, `code/06_validate_model_results.py`, `code/08_correlation_analysis.py`, `code/06_sensitivity_sweep.py`, `code/07_generate_report.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/data/processed/correlations.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/15_verify_success_criteria.py`, `code/06_sensitivity_analysis.py`, `code/13_generate_final_correlation_outputs.py`, `code/06_validate_model_results.py`, `code/08_correlation_analysis.py`, `code/06_sensitivity_sweep.py`, `code/07_generate_report.py`.
