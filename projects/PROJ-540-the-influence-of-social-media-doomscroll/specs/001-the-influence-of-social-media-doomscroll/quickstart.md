# Quickstart: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

## Prerequisites
- Python 3.11 or newer  
- Internet access (to download the verified Pew dataset)  
- GitHub Actions runner or a local Linux/macOS environment with ≥ 2 CPU cores and ≤ 6 GB RAM  

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-540-the-influence-of-social-media-doomscroll

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
# Executes: download → validation → cleaning → modeling → diagnostics → visualization
python code/main.py
```

### What the pipeline does
1. **Data ingestion** (`code/ingest.py`)  
   - Streams the verified Pew dataset URL (`https://huggingface.co/datasets/pew/social_media_anxiety`).  
   - Validates presence of required columns against `contracts/dataset.schema.yaml`.  
   - Performs listwise deletion; halts if N < 30.  

2. **Statistical modeling** (`code/model.py`)  
   - Checks construct distinctness, fits OLS, computes correlation, runs assumption diagnostics, and performs the robustness check conditioned on `social_media_engagement` correlation > 0.3.  

3. **Visualization** (`code/viz.py`)  
   - Produces `output/plots/scatter_regression.png` (scatter + regression line + 95 % CI).  

4. **Output & validation** (`code/model.py` continues)  
   - Writes `output/results/regression_results.json` (conforms to `contracts/output.schema.yaml`).  
   - Generates `outputs/success_criteria_log.txt` (plain‑text PASS/FAIL for SC‑001 – SC‑005).  

5. **Documentation & archiving** (automated by later tasks)  
   - Updates `README.md` with reproducibility notes.  
   - Archives the relevant directories into `artifacts/project_artifact.zip`.  

## Verification Checklist
- **Data file**: `data/processed/cleaned_data.csv` exists and has ≥ 30 rows.  
- **Results file**: `output/results/regression_results.json` contains keys `p_values['news_exposure_freq']`, `r_squared`, `flags`, and `runtime`.  
- **Plot**: `output/plots/scatter_regression.png` displays a regression line and shaded confidence interval.  
- **Runtime**: `runtime` ≤ 60 seconds (SC‑005).  

## Troubleshooting
| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| *Missing required columns* | None of the verified datasets contain the needed variables. | The pipeline will stop with a clear error message (FR‑001 edge case). |
| *Sample size < 30* | Too many rows removed during listwise deletion. | Review missingness; if unavoidable, the analysis cannot proceed (FR‑002 hard stop). |
| *VIF > 10* | Multicollinearity among predictors. | Examine `output/results/regression_results.json` → `vif_scores`; consider dropping the flagged variable. |
| *Robustness check skipped* | Correlation between `social_media_engagement` and `news_exposure_freq` ≤ 0.3 or variable absent. | This is expected per FR‑006; check the `flags` entry for the reason. |

---


