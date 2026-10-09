# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/01_download_data.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/generate_report.py; 5 command(s) failed: python code/01_download_data.py (rc=1); python code/02_preprocess_eeg.py (rc=1); python code/03_extract_features.py (rc=1); 23 declared deliverable(s) absent: data/interim/behavioral_exclusion_log.csv; data/interim/behavioral_metrics.csv; data/interim/correlations_raw.csv

## Failing / missing run-book commands

- python code/01_download_data.py -> rc=1
-490f-aba5-0c127a7834f2)

Repository Not Found for url: https://huggingface.co/datasets/PhysioNet/EEG-Motor-Movement-Imagery/resolve/main/S002R01.edf.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.
Downloading S002R02.edf...
Failed to download S002R02.edf: 401 Client Error. (Request ID: Root=1-6ac93904-3a390ae76bf0908746f4b8b0;11b94346-e93e-4528-b289-57be74618917)

Repository Not Found for url: https://huggingface.co/datasets/PhysioNet/EEG-Motor-Movement-Imagery/resolve/main/S002R02.edf.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.
No new files downloaded. Assuming cache or previous run.
Verifying file integrity...
ERROR: No valid files downloaded or verified.


- python code/02_preprocess_eeg.py -> rc=1
Starting EEG Preprocessing (T010)...
Error: Data directory not found at data/raw or configured paths.


- python code/03_extract_features.py -> rc=1
Starting T012: Feature Extraction with CLR Transformation
Using window=4s, overlap=0.5s
Bands: ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
Excluded participants: 0

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/03_extract_features.py", line 285, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/03_extract_features.py", line 237, in main
    subjects_eeg = load_preprocessed_eeg(eeg_dir)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/03_extract_features.py", line 44, in load_preprocessed_eeg
    raise FileNotFoundError(f"No .fif files found in {input_dir}")
FileNotFoundError: No .fif files found in /home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/data/interim/cleaned_eeg_final

- python code/04_modeling.py -> rc=1
Loading features from: /home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/data/processed/features_clr.csv
ERROR: Features file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/data/processed/features_clr.csv
Ensure T015 has completed and generated data/processed/features_clr.csv


- python code/06_sensitivity_analysis.py -> rc=1
Loading correlations data...
Error: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/data/processed/correlations.csv. Please ensure T025 (generate_final_correlation_outputs) has completed successfully.


- python code/generate_report.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/generate_report.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/interim/behavioral_exclusion_log.csv
- data/interim/behavioral_metrics.csv
- data/interim/correlations_raw.csv
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

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/behavioral_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_behavioral_parsing.py` — NOT invoked by the run-book
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/behavioral_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_behavioral_parsing.py` — NOT invoked by the run-book
    - `code/03_extract_features.py` — IS a run-book command
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
    - `code/04_extract_features.py` — NOT invoked by the run-book
    - `code/04c_relative_power.py` — NOT invoked by the run-book
    - `code/05_compute_relative_power.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/09_robustness_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/correlations_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/06_correlations.py` — NOT invoked by the run-book
    - `code/09_apply_bonferroni.py` — NOT invoked by the run-book
    - `code/10_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/correlations_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/feasibility_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/00_feasibility_filter_segments.py` — NOT invoked by the run-book
    - `code/00_feasibility_join.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/feasibility_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/feasibility_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_channels.py` — NOT invoked by the run-book
    - `code/00_feasibility_filter_segments.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/feasibility_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/final_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_channels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/final_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/final_participant_list.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_channels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/final_participant_list.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/halt_signal.json` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_channels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/halt_signal.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/joined_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/00_feasibility_filter_segments.py` — NOT invoked by the run-book
    - `code/00_feasibility_join.py` — NOT invoked by the run-book
    - `code/04_extract_psd.py` — NOT invoked by the run-book
    - `code/04c_relative_power.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/12_feasibility_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/joined_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/nonlinear_model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/08b_fit_nonlinear_model.py` — NOT invoked by the run-book
    - `code/08c_compare_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/nonlinear_model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/permutation_null_distribution.npy` is declared but was NOT written. Scripts referencing it:
    - `code/07_permutation_test.py` — NOT invoked by the run-book
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/permutation_null_distribution.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/poly_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/08a_prepare_polynomial_features.py` — NOT invoked by the run-book
    - `code/08b_fit_nonlinear_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/poly_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/psd_spectra.npy` is declared but was NOT written. Scripts referencing it:
    - `code/04_extract_psd.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/psd_spectra.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/rt_data_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/00_feasibility_join.py` — NOT invoked by the run-book
    - `code/01_download_rt_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/rt_data_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlations_corrected.csv` is declared but was NOT written. Scripts referencing it:
    - `code/09_apply_bonferroni.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlations_corrected.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_extract_features.py` — IS a run-book command
    - `code/04_extract_features.py` — NOT invoked by the run-book
    - `code/04_modeling.py` — IS a run-book command
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/04_modeling_results_final.py` — NOT invoked by the run-book
    - `code/04b_clr_transform.py` — NOT invoked by the run-book
    - `code/04c_relative_power.py` — NOT invoked by the run-book
    - `code/05_compute_relative_power.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_modeling.py` — IS a run-book command
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/04_modeling_results_final.py` — NOT invoked by the run-book
    - `code/05_modeling.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/06_validate_model_results.py` — NOT invoked by the run-book
    - `code/07_compare_robustness.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/non_linear_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/08c_compare_models.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/non_linear_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/permutation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/07_permutation_test.py` — NOT invoked by the run-book
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/permutation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_features_2s.csv` is declared but was NOT written. Scripts referencing it:
    - `code/09_robustness_features.py` — NOT invoked by the run-book
    - `code/09_robustness_modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_features_2s.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/09_robustness_modeling.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — NOT invoked by the run-book
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
    - `code/10_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/14_generate_robustness_and_sensitivity_outputs.py` — NOT invoked by the run-book
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
    - `code/10_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/11_generate_report.py` — NOT invoked by the run-book
    - `code/11a_load_results.py` — NOT invoked by the run-book
    - `code/11c_write_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
