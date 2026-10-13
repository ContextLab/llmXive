# Quickstart: Predicting Corrosion Rates with Interaction Effects

This guide shows how to run the full analysis on a fresh GitHub Actions runner (or locally).

## Prerequisites
- Python 3.11
- Git
- Internet access (to download the public dataset)

## Steps

1. **Clone the repository**
   ```bash
   git clone 
   cd corrosion-ml
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the pipeline**
   ```bash
   python -m src.pipeline.run \
       --seed 42 \
       --max-depth 5 \
       --n-estimators 200 \
       --cv-folds 5 \
       --permutes 200
   ```
   - The script will:
     1. Attempt to download and validate the dataset. If the required columns are not present, it will abort with a clear `MISSING_VARIABLE` error (FR‑001).
     2. Impute, scale, and one‑hot encode.
     3. Engineer interaction features (environment × environment and environment × composition one‑hot columns).
     4. Perform GroupKFold CV, train Full & Null models.
     5. Run a hierarchical permutation‑importance test (200 permutations) and BH correction.
     6. Compute SHAP interaction values **for the top‑10 interaction features** (by absolute SHAP magnitude) to stay within the CPU budget, and generate figures.
     7. Write `report.md` and all artifact files under `outputs/`.

4. **Inspect results**
   - Cleaned data: `data/cleaned_dataset.csv`
   - Model artifact: `outputs/model_artifact.yaml`
   - Figures: `outputs/figures/*.png`
   - Full reproducible report: `outputs/report.md`

5. **Run contract tests (optional)**
   ```bash
   pytest -k contract
   ```

## Expected Runtime & Resources
- Total wall‑time ≤ 6 h on the GitHub Actions free tier.  
- Peak RAM ≤ 7 GB (monitored automatically; fallback sampling will trigger if exceeded).  

## Re‑running with a Subset (for debugging)
```bash
python -m src.pipeline.run --sample-fraction 0.1
```
This samples [deferred] of rows (maintaining group distribution) and speeds up execution.

---



