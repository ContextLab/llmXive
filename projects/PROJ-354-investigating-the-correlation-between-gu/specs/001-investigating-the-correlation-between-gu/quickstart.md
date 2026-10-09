# Quickstart: Gut Microbiome & Cognitive Function Analysis Pipeline

## Prerequisites
- Python 3.11 or newer  
- `git`  
- At least 2 GB free disk space (synthetic data < 1 GB)  

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-354-investigating-the-correlation-between-gu

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies (pinned versions)
pip install -e .   # installs the package in editable mode
# or, if you prefer a requirements file:
pip install -r requirements.txt
```

## Running the Pipeline

### 1. Generate / Download Data
```bash
# Attempt real UK Biobank download (requires credentials in environment variables)
python code/pipelines/download.py --seed 42 --output data/raw/ukb_microbiome.parquet --cognitive-output data/raw/ukb_cognitive.parquet

# If credentials are missing, the script automatically falls back to synthetic data:
# (no additional command needed; the same call creates data/raw/synthetic_ukb.parquet)
```

### 2. Preprocess (filter + ILR)
```bash
python code/pipelines/preprocess.py \
    --input data/raw/ukb_microbiome.parquet data/raw/ukb_cognitive.parquet \
    --fallback data/raw/synthetic_ukb.parquet \
    --output data/processed/ilr_transformed.parquet
```
*Filters participants, adds a tiny pseudocount, validates against `contracts/dataset.schema.yaml`, and applies the ILR transformation.*

### 3. Core Analysis
```bash
python code/pipelines/analyze.py \
    --input data/processed/ilr_transformed.parquet \
    --output results/associations/
```
*Fits OLS, Lasso, Ridge models, performs BH correction, and runs interaction analyses.*

### 4. Visualizations
```bash
python code/paper/plots.py \
    --input results/associations/main_effects.parquet \
    --output results/plots/
```
*Produces Manhattan‑style plots with effect‑size annotations.*

### 5. Verify Results (tests)
```bash
pytest tests/ -v
```

### 6. Code Formatting & Linting
```bash
black code/
ruff check code/
```
*All files should pass without errors; any violations will be reported in `results/linting_report.txt`.*

## Output Structure

```
data/
├── raw/
│   ├── ukb_microbiome.parquet   # real data if credentials succeed
│   ├── ukb_cognitive.parquet
│   └── synthetic_ukb.parquet    # always generated as fallback
├── processed/
│   └── ilr_transformed.parquet
├── interim/               # temporary files (auto‑cleaned)

results/
├── associations/
│   ├── main_effects.parquet
│   └── interaction_effects.parquet
├── plots/
│   └── manhattan_*.png
├── sensitivity/
│   └── threshold_sweep.parquet
├── power/
│   └── power_report.txt
└── linting_report.txt
```

## Troubleshooting
- **MemoryError** – Reduce the synthetic cohort size by editing `download.py` (parameter `--n_samples`).  
- **Zero Counts** – The pipeline automatically adds a pseudocount before ILR; no manual action needed.  
- **Missing Credentials** – The script will emit a warning and generate synthetic data; real analysis will run once credentials are supplied.  

---

