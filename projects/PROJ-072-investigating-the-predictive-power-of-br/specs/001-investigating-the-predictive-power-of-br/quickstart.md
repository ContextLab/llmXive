# Quickstart: Investigating the Predictive Power of Brain Network Metrics for Schizophrenia Diagnosis

## Prerequisites

- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (or local machine with 7GB+ RAM).

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd PROJ-072-investigating-the-predictive-power-of-br
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: Ensure `nilearn`, `bctpy`, and `scikit-learn` are installed. These are CPU-optimized.*

## Running the Pipeline

### 1. Data Download (Manual Check)
Before running the full pipeline, verify the dataset is accessible.
```bash
python code/preprocessing/download_check.py
```
*This script attempts to fetch the first subject from the verified HuggingFace source. If it fails, the dataset is unavailable.*

### 2. Preprocessing (FR-001)
Process a subset of subjects (e.g., 5) to verify the pipeline.
```bash
python code/main.py --mode preprocess --subset 5
```
*Output: `data/processed/matrix_*.npy`*

### 3. Feature Extraction (FR-002, FR-003)
Compute graph metrics.
```bash
python code/main.py --mode extract_features
```
*Output: `data/processed/features.parquet`*

### 4. Classification & Validation (FR-004, FR-005)
Run the full analysis with nested CV and permutation tests.
```bash
python code/main.py --mode classify --permutations 1000
```
*Output: `data/results/model_report.json`*

## Verification

- **Check Output**: Ensure `data/results/model_report.json` contains `accuracy`, `p_value_permutation`, and `cohens_d`.
- **Sanity Check**: Run with `--random_labels` flag. Accuracy should be [deferred] and p-value > 0.05.
 ```bash
 python code/main.py --mode classify --random_labels
 ```

## Troubleshooting

- **Memory Error**: Reduce `--subset` size or ensure no other heavy processes are running.
- **Dataset Not Found**: Check `research.md` for verified URLs. The pipeline cannot proceed without the specific Schizophrenia dataset.
- **NaN in Matrix**: Increase regularization in `preprocessing/pipeline.py` (add `1e-6` to diagonal).
