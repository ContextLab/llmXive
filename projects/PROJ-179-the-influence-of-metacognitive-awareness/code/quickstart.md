# Quickstart Guide for PROJ-179

This guide outlines the steps to run the full analysis pipeline for the project "The Influence of Metacognitive Awareness on Reality Testing".

## Prerequisites

- Python 3.8+
- Required packages listed in `requirements.txt`

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Availability

**Important**: The project requires a valid behavioral dataset with `confidence_rating` and `source_label` fields.
The pipeline will check for this in T004. If no valid dataset is found, the project is blocked.

## Execution Steps

Run the following commands in order to execute the full pipeline:

1. **Check Data Availability** (T004)
 ```bash
 python code/data/validate_data_availability.py
 ```

2. **Download Dataset** (T005)
 ```bash
 python code/data/download.py
 ```

3. **Validate Dataset** (T006)
 ```bash
 python code/data/validate_data.py
 ```

4. **Preprocess Data** (T012)
 ```bash
 python code/data/preprocess.py
 ```

5. **Run Correlation Analysis** (T014)
 ```bash
 python code/src/analysis/correlation.py
 ```

6. **Run Bootstrap Analysis** (T015)
 ```bash
 python code/src/analysis/bootstrap.py
 ```

7. **Generate Primary Analysis Report** (T016)
 ```bash
 python code/src/report/generate.py
 ```

8. **Run Regression Analysis** (T020)
 ```bash
 python code/src/analysis/regression.py
 ```

9. **Run Diagnostics** (T021)
 ```bash
 python code/src/analysis/diagnostics.py
 ```

10. **Update Regression Report** (T022)
 ```bash
 python code/src/report/generate.py
 ```

11. **Filter by Modality** (T026)
 ```bash
 python code/src/analysis/filter.py
 ```

12. **Run Robustness Analysis** (T027)
 ```bash
 python code/src/analysis/robustness.py
 ```

13. **Update Robustness Report** (T028)
 ```bash
 python code/src/report/generate.py
 ```

14. **Run Quickstart Validator** (Optional)
 ```bash
 python code/quickstart_validator.py
 ```

## Output Artifacts

After successful execution, the following files should be present:

- `data/derived/trial_data.csv`
- `data/derived/visual_trials.csv`
- `data/derived/auditory_trials.csv`
- `data/results/bootstrap_config.json`
- `data/results/primary_analysis.json`
- `data/results/regression_analysis.json`
- `data/results/robustness_analysis.json`

## Troubleshooting

- If T004 fails, the project is blocked. Check the log for details.
- If any step fails, review the logs and ensure all prerequisites are met.
- For data issues, refer to the `data/validate_data_availability.py` script.

## Notes

- This pipeline is designed to run sequentially.
- Ensure sufficient computational resources for bootstrap and regression analyses.
- The project uses a Hold-Out Accuracy design for correlation analysis.