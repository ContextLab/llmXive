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
│   ├── download.py          # PubChem download
│   ├── preprocess.py        # Missing‑value handling, quality report
│   └── fingerprint.py       # Open Babel wrapper
├── models/
│   ├── baseline.py          # Crippen additive model
│   └── rf.py                # Random Forest with nested CV
├── analysis/
│   ├── stats.py             # Metrics, Wilcoxon test, LNAI
│   └── explainability.py    # SHAP, interaction heatmap, SMARTS mapping
└── main.py                  # Orchestrates the whole pipeline
data/
├── raw/
├── processed/
└── derived/
tests/
requirements.txt
pyproject.toml
.ruff.toml
```

## Running the Full Pipeline

```bash
# 1. Download raw data from PubChem
python code/data/download.py

# 2. Preprocess (handle missing values, generate quality report)
python code/data/preprocess.py

# 3. Generate fingerprints via Open Babel
python code/data/fingerprint.py

# 4. Compute baseline (Crippen) predictions
python code/models/baseline.py

# 5. Train Random Forest with nested cross‑validation
python code/models/rf.py

# 6. Perform statistical analysis and produce plots
python code/analysis/stats.py

# 7. Explainability: SHAP interaction heatmap and substructure mapping
python code/analysis/explainability.py

# 8. (Optional) Generate the comprehensive validation audit PDF
python code/analysis/validation_audit.py
```

Each script writes its outputs under `data/derived/`. The most important artifacts are:

| Artifact | Path | Description |
|----------|------|-------------|
| Baseline residual plot | `data/derived/baseline_residuals.png` |
| RF residual plot | `data/derived/rf_residuals.png` |
| SHAP interaction heatmap | `data/derived/shap_interactions.png` |
| Deviation contexts (bit‑to‑substructure) | `data/derived/deviation_contexts.csv` |
| LNAI table | `data/derived/lna_index.csv` |
| Statistical report | `data/derived/statistical_report.md` |
| Validation audit | `data/derived/validation_audit.pdf` |
| Experimental protocol | `data/derived/experimental_validation_protocol.md` |

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
- **PubChem rate limiting** – The downloader respects a 0.2 s pause between requests; increase `RATE_LIMIT` in `download.py` if you encounter HTTP 429.  
- **MemoryError** – Reduce the number of molecules processed at once (`MAX_MOLECULES` constant) or enable streaming mode (`--stream` flag).  

Enjoy reproducible molecular property prediction!
