# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python code/01_download_data.py (rc=1); python code/01_download_data.py --check-feasibility (rc=1); python code/02_preprocess_eeg.py (rc=1); 12 declared deliverable(s) absent: data/interim/behavioral_exclusion_log.csv; data/interim/behavioral_metrics.csv; data/interim/eeg_psd.csv

## Failing / missing run-book commands

- python code/01_download_data.py -> rc=1
    Starting data download for PhysioNet EEG Motor Movement/Imagery dataset...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 286, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 210, in main
    ensure_dirs(data_raw_dir)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given
- python code/01_download_data.py --check-feasibility -> rc=1
    Starting data download for PhysioNet EEG Motor Movement/Imagery dataset...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 286, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 210, in main
    ensure_dirs(data_raw_dir)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given
- python code/02_preprocess_eeg.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/02_preprocess_eeg.py", line 77, in <module>
    ) -> Tuple[Optional[mne.io.Raw], Dict[str, Any]]:
                                               ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?
- python code/03_extract_features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/03_extract_features.py", line 20, in <module>
    def load_preprocessed_eeg(input_dir: str) -> Dict[str, mne.Epochs]:
                                                 ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/04_modeling.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/04_modeling.py", line 63, in <module>
    def prepare_data(df: pd.DataFrame, feature_cols: list) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
                                                              ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?
- python code/05_robustness_analysis.py -> rc=1
    Starting Robustness Analysis (T026)...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/05_robustness_analysis.py", line 338, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/05_robustness_analysis.py", line 335, in main
    run_robustness_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/05_robustness_analysis.py", line 179, in run_robustness_pipeline
    raw_data_dir = get_path('raw_data')
                   ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 112, in get_path
    raise ValueError(f"Path '{name}' not found in config.")
ValueError: Path 'raw_data' not found in config.
- python code/06_sensitivity_analysis.py -> rc=1
    Loading correlations data...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/06_sensitivity_analysis.py", line 172, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/06_sensitivity_analysis.py", line 121, in main
    correlations_df = load_correlations()
                      ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/06_sensitivity_analysis.py", line 28, in load_correlations
    path = get_path("processed", "correlations.csv")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 2 were given
- python code/07_generate_report.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/07_generate_report.py", line 266, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/07_generate_report.py", line 222, in main
    model_results_path = get_path(base_dir, "data/processed/model_results.json")
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 2 were given

## Declared deliverables still missing

- data/interim/behavioral_exclusion_log.csv
- data/interim/behavioral_metrics.csv
- data/interim/eeg_psd.csv
- data/interim/joined_metadata.csv
- data/interim/split_indices.json
- data/processed/correlations.csv
- data/processed/features.csv
- data/processed/model_results.json
- data/processed/non_linear_comparison.json
- data/processed/robustness_report.csv
- data/processed/sensitivity_plot.png
- data/processed/verification_log.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_dirs` — defined in `code/config.py`; called 23 way(s):

- code/03_extract_features.py: ensure_dirs()
- code/07_generate_report.py: ensure_dirs(output_path.parent)
- code/04_modeling_lasso.py: output_dir = ensure_dirs("data/processed")
- code/00_feasibility_check_report.py: ensure_dirs(output_path)
- code/12_nonlinear_analysis.py: output_dir = ensure_dirs("processed")
- code/01_download_data.py: ensure_dirs(dest_path.parent)
- code/01_download_data.py: ensure_dirs(extract_to)
- code/01_download_data.py: ensure_dirs(data_raw_dir)
- code/code_03_extract_features.py: ensure_dirs(output_path)
- code/05_robustness_analysis.py: ensure_dirs([proc_data_dir])
- code/06_validate_features.py: ensure_dirs(os.path.dirname(features_path))
- code/15_verify_success_criteria.py: ensure_dirs(output_path)
- code/04_extract_behavioral_metrics.py: ensure_dirs([output_dir])
- code/13_generate_final_correlation_outputs.py: ensure_dirs(output_path)
- code/04_modeling_results_final.py: ensure_dirs(results_path)
- code/04_modeling.py: ensure_dirs()
- code/05_compute_relative_power.py: ensure_dirs(out_path)
- code/14_generate_robustness_and_sensitivity_outputs.py: ensure_dirs([args.robustness_output, args.sensitivity_output])
- code/02_preprocess_eeg.py: ensure_dirs(["interim_data"])
- code/00_feasibility_check_join.py: interim_dir = ensure_dirs("interim")
- code/00_feasibility_check_join.py: processed_dir = ensure_dirs("processed")
- code/09_apply_bonferroni.py: ensure_dirs(output_path)
- code/06_sensitivity_analysis.py: ensure_dirs(out_path)

Make `ensure_dirs` in `code/config.py` accept ALL of the above.

### `get_path` — defined in `code/config.py`; called 25 way(s):

- code/07_generate_report.py: model_results_path = get_path(base_dir, "data/processed/model_results.json")
- code/07_generate_report.py: correlations_path = get_path(base_dir, "data/processed/correlations.csv")
- code/07_generate_report.py: robustness_path = get_path(base_dir, "data/processed/robustness_report.csv")
- code/07_generate_report.py: sensitivity_plot_path = get_path(base_dir, "data/processed/sensitivity_plot.png")
- code/07_generate_report.py: verification_path = get_path(base_dir, "data/processed/verification_log.json")
- code/07_generate_report.py: metadata_path = get_path(base_dir, "data/interim/joined_metadata.csv")
- code/07_generate_report.py: output_path = get_path(base_dir, "data/processed/final_report.md")
- code/04_modeling_lasso.py: path = get_path("data/processed/features.csv")
- code/04_modeling_lasso.py: path = get_path("data/interim/split_indices.json")
- code/00_feasibility_check_report.py: status_path = get_path('interim', 'join_status.json')
- code/00_feasibility_check_report.py: output_path = get_path('processed', 'feasibility_report.md')
- code/12_nonlinear_analysis.py: features_path = get_path("processed", "features.csv")
- code/01_download_data.py: data_raw_dir = get_path("data_raw")
- code/code_03_extract_features.py: input_path = get_path(INPUT_DIR)
- code/code_03_extract_features.py: input_path = get_path(args.input_dir)
- code/code_03_extract_features.py: output_path = get_path(args.output_file)
- code/05_robustness_analysis.py: raw_data_dir = get_path('raw_data')
- code/05_robustness_analysis.py: proc_data_dir = get_path('processed_data')
- code/05_robustness_analysis.py: behavioral_path = get_path('behavioral_metrics')
- code/05_robustness_analysis.py: primary_results_path = get_path('model_results')
- code/06_validate_features.py: features_path = get_path("processed", "features.csv")
- code/15_verify_success_criteria.py: model_results_path = get_path("data/processed/model_results.json")
- code/15_verify_success_criteria.py: corr_path = get_path("data/processed/correlations.csv")
- code/15_verify_success_criteria.py: robust_path = get_path("data/processed/robustness_report.csv")
- code/15_verify_success_criteria.py: sens_plot_path = get_path("data/processed/sensitivity_plot.png")

Make `get_path` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/behavioral_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/behavioral_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
    - `code/05_compute_relative_power.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/eeg_psd.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_extract_features.py` — IS a run-book command
    - `code/code_03_extract_features.py` — NOT invoked by the run-book
    - `code/05_compute_relative_power.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/eeg_psd.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/joined_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — IS a run-book command
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/joined_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/04_modeling.py` — IS a run-book command
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — IS a run-book command
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/08_correlation_analysis.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
    - `code/09_apply_bonferroni.py` — NOT invoked by the run-book
    - `code/06_sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/correlations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_extract_features.py` — IS a run-book command
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/code_03_extract_features.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/06_validate_features.py` — NOT invoked by the run-book
    - `code/08_correlation_analysis.py` — NOT invoked by the run-book
    - `code/04_modeling_results_final.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — IS a run-book command
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/04_modeling_results_final.py` — NOT invoked by the run-book
    - `code/04_modeling.py` — IS a run-book command
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/non_linear_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/non_linear_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — IS a run-book command
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/14_generate_robustness_and_sensitivity_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — IS a run-book command
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/14_generate_robustness_and_sensitivity_outputs.py` — NOT invoked by the run-book
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/verification_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — IS a run-book command
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/verification_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
