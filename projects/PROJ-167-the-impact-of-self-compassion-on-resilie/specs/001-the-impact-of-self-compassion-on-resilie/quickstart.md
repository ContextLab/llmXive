# Quickstart: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Prerequisites

- Git ≥ 2.40  
- Python 3.11 (or later)  
- Internet access (to download the OSF dataset)  

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourorg/self-compassion-feedback.git
cd self-compassion-feedback

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Run the Full Pipeline

```bash
# Set reproducible seed (FR-012)
export PYTHONHASHSEED=42

# Execute the analysis driver
python -m src.main
```

The driver performs the following steps automatically:

1. Downloads `data/raw/osf_dataset.csv` (FR‑001).  
2. Cleans the data → `data/clean/cleaned_osf.parquet` (FR‑002‑FR‑004).  
3. Fits ANCOVA models for anxiety, rumination, and self‑efficacy (FR‑005‑FR‑006).  
4. Computes HC3 robust SEs and flags heteroskedasticity (FR‑009).  
5. Runs bootstrap robustness (FR‑008) and alternative‑moderator analysis (FR‑014).  
6. Generates simple‑slope PNGs under `results/plots/`.  
7. Produces `results/report.html` (FR‑010).  

## Verify Success

- **Regression tables**: check `results/models/*.json` for the interaction term `C(feedback)[T.2]:SCS_z`.  
- **Bootstrap**: ensure `bootstrap_ci` fields are present and non‑zero.  
- **Plots**: three PNG files per outcome in `results/plots/`.  
- **HTML report**: open `results/report.html` in Chrome/Firefox; all sections should render without errors.  

## Testing (Contract Validation)

```bash
pytest -q
```

All contract tests should pass, confirming that the output conforms to `contracts/analysis_result.schema.yaml`.

---
