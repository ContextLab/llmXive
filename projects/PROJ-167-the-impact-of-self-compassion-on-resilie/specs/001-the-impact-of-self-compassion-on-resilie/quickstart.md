# Quickstart: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Prerequisites
- **Python** 3.11 (or later) installed.  
- **Git** to clone the repository.  
- **Internet** access to download the OSF dataset (≈ 2 MB) that includes the required outcome measures.

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

## Running the Full Pipeline

```bash
# Set the random seed (ensured by the script, but can be overridden)
export PYTHONHASHSEED=42

# Execute the end‑to‑end analysis
python src/main.py run_all
```

The command performs, in order:

1. **Download** the raw OSF Parquet (`data/raw/osf_feedback.parquet`).  
2. **Compute and record** a SHA‑256 checksum of the downloaded file (Principle III).  
3. **Clean** the data, produce `data/clean/cleaned_osf.csv`.  
4. **Fit** ANCOVA models for anxiety, rumination, and self‑efficacy (including robust HC3 SEs).  
5. **Bootstrap** the interaction term (5 000 resamples).  
6. **Run** robustness analysis with the rumination subscale.  
7. **Generate** simple‑slope PNGs (`outputs/figures/*.png`).  
8. **Create** the HTML report (`outputs/report.html`).  

All artefacts are logged in `outputs/logs/` and checksummed in `state/projects/...yaml`.

## Verifying the Result (Contract Test)

```bash
pytest tests/contract/test_analysis_result.py
```

The test loads `outputs/analysis/analysis_result.json` and validates it against `contracts/analysis_result.schema.yaml`. A passing test confirms that:

- The interaction coefficient is present with a p‑value < 0.05 (SC‑001).  
- Partial η² ≥ 0.02 (SC‑002).  
- Bootstrap CI excludes zero and overlaps the parametric CI (SC‑003).  
- Simple‑slope PNGs exist for each outcome with three distinct lines (SC).  
- The HTML report renders in Chrome/Firefox and includes all required sections (SC‑005).

## Common Issues

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| “Dataset not found” error | OSF URL changed or network block | Verify connectivity; the script falls back to the verified OSF URL. |
| “Insufficient sample size” abort | After cleaning < 92 participants remain | Review missing‑data log; consider relaxing exclusion criteria only after ethical review. |
| “Heteroskedasticity flag = true” | Breusch‑Pagan p < 0.10 | Results are still reported; note the flag in the HTML report. |
