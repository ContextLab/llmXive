# Quickstart: Molecular Property Prediction Pipeline

## Prerequisites
- Python 3.10 or newer
- Open Babel CLI (`obabel`) in your `PATH`
- Git

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/PROJ-324-predicting-molecular-properties-from-ope.git
cd PROJ-324-predicting-molecular-properties-from-ope

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Open Babel (CLI)
# Ubuntu/Debian
sudo apt-get install openbabel
# macOS
brew install open-babel
# Windows: download installer from https://openbabel.org/
```

## Directory Overview

```text
code/
├── data/
│   ├── download.py          # PubChem download & checksum
│   ├── preprocess.py        # Missing‑value handling, quality report, experimental‑only filter
│   └── fingerprint.py       # Open Babel wrapper
├── models/
│   ├── baseline.py          # Property‑specific additive baselines
│   └── rf.py                # Random Forest with nested CV
├── analysis/
│   ├── stats.py             # Metrics, Wilcoxon test, LNAI, verification log
│   └── explainability.py    # SHAP, interaction validation, MACCS‑SMARTS mapping, test‑set export
└── main.py                  # Orchestrates the whole pipeline
data/
├── raw/
├── processed/
└── derived/
tests/
requirements.txt
pyproject.toml
.ruf.toml
```

## Running the Full Pipeline

```bash
# 1. Download raw data from PubChem (includes verification log)
python code/data/download.py

# 2. Preprocess (handle missing values, filter to experimental records, generate quality report)
python code/data/preprocess.py

# 3. Generate fingerprints via Open Babel
python code/data/fingerprint.py

# 4. Compute additive baselines (logP, solubility, boiling point)
python code/models/baseline.py

# 5. Train Random Forest with nested cross‑validation
python code/models/rf.py

# 6. Perform statistical analysis and produce plots
python code/analysis/stats.py

# 7. Explainability: SHAP values, interaction matrix, permutation validation,
#    map MACCS bits to SMARTS, export test‑set split
python code/analysis/explainability.py

# 8. (Optional) Generate the validation summary CSV
python code/analysis/validation_summary.py
```

Each script writes its outputs under `data/derived/`. The most important artifacts are:

| Artifact | Path | Description |
|----------|------|-------------|
| Raw PubChem CSV | `data/raw/pubchem.csv` |
| Data quality report | `data/derived/data_quality_report.csv` |
| Verification log | `data/derived/verification_log.txt` |
| Fingerprint arrays | `data/processed/*.npy` |
| Baseline predictions | `data/derived/baseline_predictions.csv` |
| Baseline residual plot | `data/derived/baseline_residuals.png` |
| RF predictions | `data/derived/rf_predictions.csv` |
| RF residual plot | `data/derived/rf_residuals.png` |
| Test‑set split | `data/derived/test_set.csv` |
| Statistical report | `data/derived/statistical_report.md` |
| SHAP values (JSON) | `data/derived/predictions/*.json` |
| SHAP interaction heatmap | `data/derived/shap_interactions.png` |
| SHAP interaction matrix (raw) | `data/derived/shap_interaction.npy` |
| SHAP interaction validation | `data/derived/shap_interaction_validation.txt` |
| Top‑K MACCS bits list | `data/derived/top_k_maccs.txt` |
| LNAI table | `data/derived/lna_index.csv` |
| Deviation contexts (MACCS‑SMARTS) | `data/derived/deviation_contexts.csv` |
| Validation summary | `data/derived/validation_summary.csv` |

All artifacts are validated against the JSON/YAML contracts in `contracts/`.

## Testing

```bash
pytest tests/
```

## Linting & Formatting

```bash
ruff check code/
black --check code/
# To auto‑fix:
black code/
ruff check --fix code/
```

## Troubleshooting

- **`obabel` not found** – Ensure the Open Babel executable is in your `PATH`.  
- **PubChem rate limiting** – The downloader respects a brief pause between requests; increase `RATE_LIMIT` in `download.py` if you encounter an HTTP rate‑limit error.  
- **MemoryError** – Reduce the number of molecules processed at once (`MAX_MOLECULES` constant) or enable streaming mode (`--stream` flag).  

Enjoy reproducible molecular property prediction!

---


