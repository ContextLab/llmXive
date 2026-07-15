# Quickstart Guide: Predicting Cognitive Fatigue from Resting-State EEG

## Prerequisites

- Python 3.11+
- pip (package manager)

## Setup

1. **Create and activate virtual environment:**
 ```bash
 cd projects/PROJ-470-predicting-cognitive-fatigue-from-restin
 python -m venv code/venv
 source code/venv/bin/activate # On Windows: code\venv\Scripts\activate
 ```

2. **Install dependencies:**
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Verify environment:**
 ```bash
 python code/check_env.py
 ```

## Pipeline Execution

Run the full analysis pipeline in order:

```bash
# 1. Download and validate data
python code/download.py

# 2. Preprocess EEG data (filtering, artifact rejection)
python code/preprocess.py

# 3. Extract complexity features (LZC, Permutation Entropy)
python code/features.py

# 4. Run correlation analysis and FDR correction
python code/analysis.py

# 5. Run sensitivity analysis
python code/sensitivity_analysis.py

# 6. Generate final report
python code/report.py
```

## Output Files

After successful execution, the following files will be generated:

- `data/processed/preprocessed_eeg.npy`: Cleaned EEG data
- `data/processed/lzc_metrics.csv`: Lempel-Ziv complexity metrics per channel
- `data/processed/pe_metrics.csv`: Permutation entropy metrics per channel
- `data/processed/complexity_metrics.csv`: Combined complexity metrics
- `data/analysis/correlation_results.csv`: Statistical correlation results
- `data/analysis/sensitivity_table.csv`: Sensitivity analysis at p≤0.05 and p≤0.01
- `data/report/final_report.txt`: Comprehensive analysis report

## Validation

To validate the pipeline on CPU-only CI:
```bash
python code/validate_quickstart.py
```

## Troubleshooting

- **Missing datasets**: Ensure `code/config.yaml` has correct dataset IDs
- **Memory errors**: The pipeline uses streaming to stay under 6GB RAM
- **Import errors**: Verify virtual environment is activated and requirements installed