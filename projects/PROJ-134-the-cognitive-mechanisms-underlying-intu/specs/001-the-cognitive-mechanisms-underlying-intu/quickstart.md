# Quickstart: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

## Prerequisites
- Python 3.11+
- Git
- (Optional) Kaggle account for GPU offload (automated by CI if CPU fails).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-134-the-cognitive-mechanisms-underlying-intu
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: This installs PyMC5, PyTensor, and all data processing libraries.*

## Running the Pipeline

### Option A: Real Data Mode (Recommended)
This mode fetches real MFQ data from the verified OSF source and generates simulated VR logs.
```bash
# T090: Ensure spec amendment is approved
python -c "import os; assert os.path.exists('specs/001-the-cognitive-mechanisms-underlying-intu/spec_amendment_FR006.md') and 'APPROVED' in open('specs/001-the-cognitive-mechanisms-underlying-intu/spec_amendment_FR006.md').read(), 'T095: Amendment not found or not approved'"

# T092: Fetch real VR config (or fail)
python code/fetch_real_vr.py --mode real

# Fetch real MFQ data
python code/fetch_real_data.py --mode real

# T014: Generate synthetic VR logs (T092 fallback if real VR unavailable)
python code/simulate_vr.py --salience low --salience high --n-samples 1000

# Preprocess and merge
python code/preprocessing.py

# Run Bayesian model
python code/models/bayesian_model.py

# Run comparison and sensitivity
python code/analysis/comparison.py
python code/analysis/sensitivity.py
python code/analysis/bonferroni.py
```
*If the real data source is unreachable or schema validation fails, the script will raise a `DataUnavailableError` and stop. No synthetic data will be generated for the MFQ component.*

### Option B: Simulation Mode (Development Only)
Generates fully synthetic data for structural validation.
```bash
python code/simulate_vr.py --salience low --salience high --n-samples 1000 --mode full-synthetic
python code/preprocessing.py --mode synthetic
python code/models/bayesian_model.py --mode synthetic
```
*Note: Results from Simulation Mode are for structural validation only and must not be used for final research conclusions.*

## Verifying Results
1. Check `data/processed/synthetic_logs.csv` for the generated VR logs (T014).
2. Check `data/processed/merged_analysis.parquet` for the cleaned dataset.
3. Review `results/posterior_summary.csv` for the Bayesian model outputs.
4. Inspect `results/waic_comparison.json` for model comparison metrics.
5. Ensure `state/...yaml` has updated checksums for all new artifacts.

## Troubleshooting
- **OOM Error**: If you run out of memory, the pipeline will automatically attempt to sample a smaller subset. For full data, ensure you are on a Kaggle GPU environment (automated by CI).
- **PyMC5 Import Error**: Ensure `pymc>=5.0.0` is installed. You may need to update `pytensor`.
- **Data Not Found**: If the script fails to find the OSF dataset, verify your internet connection. The script will not fall back to synthetic data for MFQ.
- **T095 Failure**: If the spec amendment file is missing or lacks "APPROVED", the pipeline will halt.
