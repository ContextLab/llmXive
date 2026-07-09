# Quickstart: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Prerequisites

- Python 3.11+
- API Keys for Materials Project (if available)
- ~8 GB free disk space

## Installation

1. **Clone and Setup**:
   ```bash
   cd projects/PROJ-443-predicting-the-effect-of-alloying-on-the
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Create `code/config.py` or set environment variables:
   ```bash
   export MP_API_KEY="your_key_here"
   ```

## Running the Pipeline

Execute the full pipeline (Fetch -> Process -> Train -> Evaluate -> Report):

```bash
python code/main_pipeline.py
```

### Step-by-Step Execution

1. **Data Fetch**:
   ```bash
   python code/data/fetch_hea_data.py
   ```
   - Downloads from OQMD (verified URLs) and Materials Project.
   - Generates `data/source_metadata.yaml` (includes API versions).
   - **Halts** if < 500 samples.

2. **Feature Engineering**:
   ```bash
   python code/data/preprocess.py
   ```
   - Applies ILR transformation.
   - Calculates Residual Bulk Modulus.
   - **Excludes** Miedema features if predicting Residual.

3. **Validation Check**:
   ```bash
   python code/data/validate.py
   ```
   - Checks residual vs. descriptor correlation (Warning if $|r| > 0.1$).

4. **Model Training & Evaluation**:
   ```bash
   python code/models/train.py
   python code/models/evaluate.py
   ```
   - Runs RF, GB, ElasticNet.
   - Performs Grouped Bootstrap (sufficient iterations).
   - Computes FDR-corrected p-values.
   - Runs Permutation Test for Type I error (Thresholds: a range of values).

5. **Report Generation**:
   ```bash
   python code/reports/generate_report.py
   ```
   - Outputs `results/report.md` with SHAP plots and **Associational Disclaimer**.

## Expected Outputs

- `data/processed/hea_dataset.csv`: Cleaned dataset.
- `data/source_metadata.yaml`: Provenance record.
- `results/metrics.yaml`: Performance metrics.
- `results/report.md`: Final scientific summary.

## Troubleshooting

- **"Retrieved [N] samples; threshold 500 not met"**: The public datasets did not provide enough HEA samples. The pipeline halts to prevent underpowered analysis.
- **"Insufficient groups for grouped bootstrap"**: A limited number of unique element sets are expected to be found. Proceeds with standard bootstrap (warning logged).
- **"Potential confound detected"**: Residuals correlate with a descriptor. Proceeds with caution; check `results/report.md` for notes.
- **"Bulk Modulus not found in dataset"**: The verified OQMD dataset lacks the required target variable. The pipeline halts.