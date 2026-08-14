# Quickstart Guide

This guide runs the full pipeline end-to-end.
Ensure `data/raw` is populated by `code/01_download_data.py` first.

## Prerequisites
- Python 3.8+
- Dependencies: `pip install -r code/requirements.txt`

## Execution Order
The following commands must be run in order. Each step depends on the previous one.

1. **Download Data** (T007)
 ```bash
 python code/01_download_data.py
 ```

2. **Feasibility Check** (T008a)
 ```bash
 python code/00_feasibility_check_join.py
 ```

3. **Preprocess EEG** (T010a, T010b)
 ```bash
 python code/02_preprocess_eeg.py
 ```

4. **Extract EEG Features** (T012)
 ```bash
 python code/03_extract_features.py
 ```

5. **Extract Behavioral Metrics** (T013) - **NEW**
 ```bash
 python code/04_extract_behavioral_metrics.py
 ```

6. **Compute Relative Power & CLR** (T015)
 ```bash
 python code/05_compute_relative_power.py
 ```

7. **Modeling** (T017, T018, T019)
 ```bash
 python code/04_modeling.py
 ```

8. **Correlation Analysis** (T020, T021)
 ```bash
 python code/08_correlation_analysis.py
 ```

9. **Non-linear Analysis** (T024)
 ```bash
 python code/12_nonlinear_analysis.py
 ```

10. **Robustness Analysis** (T026a-d)
 ```bash
 python code/05_robustness_analysis.py
 ```

11. **Sensitivity Analysis** (T028a-b)
 ```bash
 python code/06_sensitivity_analysis.py
 ```

12. **Generate Final Report** (T031)
 ```bash
 python code/07_generate_report.py
 ```

13. **Verify Success Criteria** (T032)
 ```bash
 python code/15_verify_success_criteria.py
 ```

## Outputs
- `data/interim/behavioral_metrics.csv`
- `data/interim/behavioral_exclusion_log.csv`
- `data/processed/features.csv`
- `data/processed/model_results.json`
- `data/processed/final_report.md`