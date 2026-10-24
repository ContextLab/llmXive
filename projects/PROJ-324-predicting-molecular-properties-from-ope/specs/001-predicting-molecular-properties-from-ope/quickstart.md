# Quickstart: Molecular Property Prediction Pipeline

## Prerequisites
- Python 3.10 or newer
- Open Babel CLI (`obabel`) in your `PATH`
- Git
- (Optional) `make` for convenience

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
│   ├── preprocess.py        # Quality filtering, experimental‑only flag
│   └── fingerprint.py       # Open Babel wrapper (MACCS, ECFP4)   # FP2 removed
├── models/
│   ├── baseline.py          # Property‑specific additive baselines
│   └── rf.py                # Random Forest with nested CV
├── analysis/
│   ├── stats.py             # Metrics, Wilcoxon test, LNAI, precision/recall, power analysis
│   └── explainability.py    # SHAP, bootstrap interaction validation, SMARTS mapping, report generation
└── main.py                  # Orchestrates the whole pipeline
data/
├── raw/
├── processed/
└── derived/
reference/
└── substructures.yaml       # Curated substructure reference set
tests/
requirements.txt
pyproject.toml
.ruf.toml
```

## Running the Full Pipeline

```bash
# 1. Download raw experimental data from PubChem
python code/data/download.py

# 2. Preprocess: filter to experimental records, enforce quality thresholds
python code/data/preprocess.py

# 3. Generate MACCS and ECFP4 fingerprints (FP2 omitted)
python code/data/fingerprint.py

# 4. Compute additive baselines for each property
python code/models/baseline.py

# 5. Train Random Forest with nested k‑fold cross‑validation
python code/models/rf.py

# 6. Perform statistical comparison (Wilcoxon test) and create residual plots
python code/analysis/stats.py

# 7. Explainability workflow:
#    - SHAP values & interaction matrix
#    - Bootstrap validation of interactions (several resamples)
#    - Top‑K MACCS selection (inner‑validation folds only)
#    - LNAI computation (several thousand permutations, main‑effect adjusted, BH FDR)
#    - SMARTS mapping for **all** selected bits
#    - Precision/Recall evaluation
#    - Interaction‑Zone Report PDF
#    - Expert validation PDF
python code/analysis/explainability.py

# 8. Generate schema‑compliant outputs
python code/analysis/generate_schema_outputs.py   # creates predictions_schema.csv & molecules_schema.csv

# 9. Compile the final validation audit (checksums, data‑quality report, verification log, residual plots, LNAI tables, SHAP validation, mapping metrics, per‑molecule LNAI, expert review)
python code/analysis/validation_audit.py
```

Each script writes its outputs under `data/derived/`. Key artifacts include:

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
| SHAP values (JSON) | `data/derived/shap/*.json` |
| SHAP interaction heatmap | `data/derived/shap_interactions.png` |
| SHAP interaction matrix (raw) | `data/derived/shap_interaction.npy` |
| SHAP interaction validation | `data/derived/shap_interaction_validation.txt` |
| Top‑K MACCS bits (selection‑set) | `data/derived/top_k_maccs_selection.txt` |
| Top‑K MACCS bits (test‑set) | `data/derived/top_k_maccs_test.txt` |
| LNAI table | `data/derived/lna_index.csv` |
| Per‑molecule LNAI | `data/derived/lna_index_per_molecule.csv` |
| Deviation contexts (SMARTS) | `data/derived/deviation_contexts.csv` |
| Mapping metrics (precision/recall) | `data/derived/mapping_metrics.txt` |
| Interaction‑Zone Report | `data/derived/interaction_zone_report.pdf` |
| Expert Validation Report | `data/derived/validation_report.pdf` |
| Validation Audit | `data/derived/validation_audit.pdf` |
| Predictions schema CSV | `data/derived/predictions_schema.csv` |
| Molecules schema CSV | `data/derived/molecules_schema.csv` |
| Validation summary (checksums, QC, etc.) | `data/derived/validation_summary.csv` |

All artifacts are validated against the JSON/YAML contracts in `contracts/`.

## Testing

```bash
pytest tests/
```

## Linting & Formatting

```bash
ruff check code/
black --check code/
# Auto‑fix:
black code/
ruff check --fix code/
```

## Troubleshooting

- **`obabel` not found** – Ensure the Open Babel executable is in your `PATH`.  
- **PubChem rate limiting** – `download.py` includes a configurable `RATE_LIMIT` pause; increase it if you hit HTTP 429 errors.  
- **MemoryError** – Reduce the batch size or enable streaming mode (`--stream` flag) in `download.py`.  

Enjoy reproducible molecular property prediction!  

---



