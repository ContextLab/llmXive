# Quickstart: The Effect of Anticipated Regret on Choice Deferral

## Prerequisites
- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository** (assuming standard structure):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-113-the-effect-of-anticipated-regret-on-choi
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Setup

1. **Download Raw Data**:
   The `code/ingest.py` script will automatically download data from the verified HuggingFace URLs.
   ```bash
   python code/ingest.py --download-only
   ```
   *Note: This will create `data/raw/` and verify checksums.*

2. **Verify Data Integrity**:
   ```bash
   python code/ingest.py --verify
   ```

## Running the Pipeline

### Step 1: Feature Engineering
Compute the regret proxy and clean the data.
```bash
python code/features.py
```
*Output: `data/processed/trials_with_proxy.csv`*

### Step 2: Primary Analysis
Fit the mixed-effects model and calculate VIF.
```bash
python code/modeling.py
```
*Output: `results/coefficients.csv`, `results/vif_report.csv`*

### Step 3: Robustness & Sensitivity
Run the secondary dataset analysis and sensitivity sweeps.
```bash
python code/robustness.py
```
*Output: `results/robustness_report.csv`*

### Step 4: Generate Report
Compile all results into a summary.
```bash
python code/main.py --full-pipeline
```

## Testing

Run unit tests for feature calculation:
```bash
pytest tests/unit/test_features.py
```

Run contract validation tests:
```bash
pytest tests/contract/test_schemas.py
```

## Troubleshooting

- **Memory Error**: If processing large datasets, ensure `chunksize` is used in `ingest.py`.
- **Convergence Issues**: If the mixed-effects model fails to converge, check for singular fits (single-trial participants) and apply the fallback logic defined in `modeling.py`.
- **Missing Dependencies**: Ensure `statsmodels` and `pandas` are installed.
