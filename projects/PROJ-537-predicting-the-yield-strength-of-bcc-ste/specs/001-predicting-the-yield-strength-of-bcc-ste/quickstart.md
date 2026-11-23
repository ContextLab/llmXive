# Quickstart: Predicting the Yield Strength of BCC Steels from Density Functional Theory

## Prerequisites
- **Python 3.11** (or newer)  
- **Materials Project API key** (free registration at <https://materialsproject.org>)  
- Internet access (for downloading the experimental dataset and querying the Materials Project API)  

## Installation
```bash
# 1. Clone the repository
git clone <repository-url>
cd PROJ-537-predicting-the-yield-strength-of-bcc-ste

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Configuration
```bash
# Export your Materials Project API key
export MP_API_KEY="YOUR_API_KEY_HERE"
# (Optional) Set a fixed random seed for reproducibility
export RANDOM_SEED=42
```

## Running the Full Pipeline
```bash
# This single command runs the entire research pipeline end‑to‑end,
# producing the merged dataset, trained models, interpretability
# analyses, and the final JSON results as well as PNG figures.
python code/run_all.py
```

### What the script does
1. **Download experimental BCC composition data** from the verified MatNavi URL (`datasets.load_dataset('matnavi/steel_yield_strength')`).  
2. **Query the Materials Project API** for elastic constants of each formula, filtering for BCC (`space_group_number == 229`).  
3. **Merge** the two sources; if fewer than **20** rows survive, the script **halts with `ERR_INSUFFICIENT_DATA`**.  
4. **Engineer features**, compute VIF, and calculate Pearson correlation (SC‑001).  
5. **Train** a Random Forest with composition + DFT features and a composition‑only baseline using **nested 5‑fold cross‑validation**.  
6. **Perform** a paired **t‑test** on the outer‑fold MAE differences, compute effect size, 95 % CI, and calculate statistical power (SC‑008).  
7. **Run** TreeSHAP, permutation importance, and a **full‑dataset bootstrap stability** analysis (SC‑004, SC‑005).  
8. **Write** `data/results/output.json` (validated against `contracts/output.schema.yaml` and `contracts/model_output.schema.yaml`) and save diagnostic plots under `data/results/plots/`.  

## Verifying the Results
- Open `data/results/output.json` and confirm that:
  - `"data_validation":{"row_count":<int>,"min_threshold_met":true}`  
  - `"metrics"` contains `r2_rf`, `mae_rf`, `r2_baseline`, `mae_baseline`, `p_value`, `power`, `null_hypothesis`.  
- Run the contract tests:
```bash
pytest -q tests/contract/
```
All tests should pass; any failure indicates a schema mismatch.

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `ERR_INSUFFICIENT_DATA` | The merged dataset has < 20 rows (no yield‑strength column or too many missing DFT matches). | Verify that the MatNavi dataset actually contains a `yield_strength_MPa` column. If not, the project cannot proceed per the specification. |
| `MP_API_KEY not set` | Environment variable missing. | Export `MP_API_KEY` before running. |
| API rate‑limit errors | Too many rapid queries. | The script already includes exponential backoff; rerun after a short pause. |
| Missing PNGs (`shap_summary.png`, `stability_distribution.png`) | One of the interpretability steps failed. Check the logs for the failing step and ensure all required dependencies are installed. |
| MemoryError | Unlikely with ≤ 50 rows; if present, ensure no other heavy processes are running on the CI runner. | Reduce concurrent jobs or run locally with more memory. |