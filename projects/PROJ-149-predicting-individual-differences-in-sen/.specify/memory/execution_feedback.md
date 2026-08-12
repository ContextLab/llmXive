# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/04_extract_behavioral_metrics.py: synthetic/fake INPUT data not authorized by the spec — “…nnotations, we'll create synthetic data             # based on t…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/04_extract_behavioral_metrics.py: synthetic/fake INPUT data not authorized by the spec — “…nnotations, we'll create synthetic data             # based on t…”; 8 command(s) failed: python code/01_download_data.py (rc=1); python code/01_download_data.py --check-feasibility (rc=1); python code/02_preprocess_eeg.py (rc=1); 12 declared deliverable(s) absent: data/interim/behavioral_exclusion_log.csv; data/interim/behavioral_metrics.csv; data/interim/eeg_psd.csv

## Failing / missing run-book commands

- python code/01_download_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 32, in <module>
    from config import get_path, ensure_dirs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 128, in <module>
    _CONFIG = load_config()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in load_config
    _CONFIG = _deep_merge(_CONFIG, custom_config)
                          ^^^^^^^
UnboundLocalError: cannot access local variable '_CONFIG' where it is not associated with a value
- python code/01_download_data.py --check-feasibility -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/01_download_data.py", line 32, in <module>
    from config import get_path, ensure_dirs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 128, in <module>
    _CONFIG = load_config()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in load_config
    _CONFIG = _deep_merge(_CONFIG, custom_config)
                          ^^^^^^^
UnboundLocalError: cannot access local variable '_CONFIG' where it is not associated with a value
- python code/02_preprocess_eeg.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/02_preprocess_eeg.py", line 23, in <module>
    from config import get_path, ensure_dirs, get_filter_params, get_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 128, in <module>
    _CONFIG = load_config()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in load_config
    _CONFIG = _deep_merge(_CONFIG, custom_config)
                          ^^^^^^^
UnboundLocalError: cannot access local variable '_CONFIG' where it is not associated with a value
- python code/03_extract_features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/03_extract_features.py", line 29, in <module>
    from config import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 128, in <module>
    _CONFIG = load_config()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in load_config
    _CONFIG = _deep_merge(_CONFIG, custom_config)
                          ^^^^^^^
UnboundLocalError: cannot access local variable '_CONFIG' where it is not associated with a value
- python code/04_modeling.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/04_modeling.py", line 19, in <module>
    from config import set_global_seed, get_seed, get_path, ensure_dirs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 128, in <module>
    _CONFIG = load_config()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in load_config
    _CONFIG = _deep_merge(_CONFIG, custom_config)
                          ^^^^^^^
UnboundLocalError: cannot access local variable '_CONFIG' where it is not associated with a value
- python code/05_robustness_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/05_robustness_analysis.py", line 30, in <module>
    from config import get_path, get_band_freqs, get_all_band_names, get_filter_params, ensure_dirs, get_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 128, in <module>
    _CONFIG = load_config()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in load_config
    _CONFIG = _deep_merge(_CONFIG, custom_config)
                          ^^^^^^^
UnboundLocalError: cannot access local variable '_CONFIG' where it is not associated with a value
- python code/06_sensitivity_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/06_sensitivity_analysis.py", line 24, in <module>
    from config import get_path, ensure_dirs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 128, in <module>
    _CONFIG = load_config()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in load_config
    _CONFIG = _deep_merge(_CONFIG, custom_config)
                          ^^^^^^^
UnboundLocalError: cannot access local variable '_CONFIG' where it is not associated with a value
- python code/07_generate_report.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/07_generate_report.py", line 29, in <module>
    from config import get_path, ensure_dirs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 128, in <module>
    _CONFIG = load_config()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-149-predicting-individual-differences-in-sen/code/config.py", line 69, in load_config
    _CONFIG = _deep_merge(_CONFIG, custom_config)
                          ^^^^^^^
UnboundLocalError: cannot access local variable '_CONFIG' where it is not associated with a value

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

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/behavioral_exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/behavioral_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_compute_relative_power.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/04_extract_behavioral_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/behavioral_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/eeg_psd.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_compute_relative_power.py` — NOT invoked by the run-book
    - `code/03_extract_features.py` — IS a run-book command
    - `code/code_03_extract_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/eeg_psd.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/joined_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_feasibility_check_join.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/joined_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/04_modeling.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/08_correlation_analysis.py` — NOT invoked by the run-book
    - `code/06_sensitivity_analysis.py` — IS a run-book command
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
    - `code/09_apply_bonferroni.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — IS a run-book command
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
    - `code/08_correlation_analysis.py` — NOT invoked by the run-book
    - `code/05_compute_relative_power.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/04_modeling_results_final.py` — NOT invoked by the run-book
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/03_extract_features.py` — IS a run-book command
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/10_perform_permutation_test.py` — NOT invoked by the run-book
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/04_modeling_results_final.py` — NOT invoked by the run-book
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/04_modeling_lasso.py` — NOT invoked by the run-book
    - `code/04_modeling.py` — IS a run-book command
    - `code/07_generate_report.py` — IS a run-book command
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/non_linear_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/12_nonlinear_analysis.py` — NOT invoked by the run-book
    - `code/13_generate_final_correlation_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/non_linear_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_robustness_analysis.py` — IS a run-book command
    - `code/14_generate_robustness_and_sensitivity_outputs.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — IS a run-book command
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/14_generate_robustness_and_sensitivity_outputs.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — IS a run-book command
    - `code/07_generate_sensitivity_plot.py` — NOT invoked by the run-book
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/verification_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/07_generate_report.py` — IS a run-book command
    - `code/15_verify_success_criteria.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/verification_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
