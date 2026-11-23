# Quickstart: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

## Prerequisites
- Python 3.11 or newer  
- Internet access (to download the three verified parquet files **or** a future open‑access survey dataset that contains the required variables)  
- Linux/macOS environment with at least 2 CPU cores (GitHub Actions free‑tier runner)  
- No GPU required  

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-540-the-influence-of-social-media-doomscroll
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
python code/main.py
```

### What the pipeline does
1. **Power analysis** – computes the minimum sample size needed to detect a **standardized** β ≥ 0.10 (or f² ≥ 0.02) for `news_exposure_freq` using `statsmodels.stats.power.FTestPower` (df_num=1). If the projected N after cleaning would be insufficient, the run stops with an “Insufficient Power” error.  
2. **Ingestion** (`code/ingest.py`): downloads the three verified parquet URLs, computes SHA‑256 checksums, and validates each against the required schema **including all mandatory fields** (see `contracts/dataset.schema.yaml`).  
   - **Current expected outcome**: because none of the files contain the required survey variables, the pipeline writes `output/results/regression_results.json` with `data_status = "HALTED_NO_VALID_DATASET"` and a detailed `halt_report`, then stops.  
   - **Future scenario**: when a suitable open dataset (e.g., a Pew Research “Social Media Use & Mental Health” CSV hosted on HuggingFace) becomes available, the pipeline proceeds to cleaning and analysis.  
3. **Missingness assessment** – runs Little’s MCAR test; if MCAR fails **and** missingness ≤ 10 % for the predictor/outcome, binary missingness indicators are added and a 10‑fold `IterativeImputer` is used as a **sensitivity** analysis (listwise deletion remains primary).  
4. **Proxy construct validation** – if `proxy_flag=True`, performs exploratory factor analysis on anxiety items; requires loading ≥ 0.4 on an anticipatory‑anxiety factor **and** the instrument be on the whitelist. If the proxy instrument is not validated, the run halts.  
5. **Distinctness/VIF check** – loads `variable_metadata.csv` to confirm distinct instruments; retains `baseline_anxiety` **only if** distinct, otherwise drops it and flags a warning (addressing coupling risk).  
6. **Export cleaned CSV** – writes `data/processed/cleaned_survey.csv` (used by verification scripts).  
7. **Modeling** (`code/model.py`): **standardizes** `news_exposure_freq`, fits an OLS regression with covariates `news_exposure_freq_std`, `baseline_anxiety` (if retained), `social_media_engagement` (if present), `age`, and one‑hot `gender`.  
8. **Correlation** – selects Pearson or Spearman based on normality of `news_exposure_freq_std` and `anxiety_score`.  
9. **Assumption checks** – computes VIF, Breusch‑Pagan, residual‑vs‑fitted linearity, and residual normality; stores PASS/FAIL **and** raw p‑values. If any assumption p‑value ≤ 0.05 the pipeline aborts (SC‑004).  
10. **Robustness checks** – (a) high‑engagement subset (|r| > 0.3) with **sign‑and‑significance consistency verification** (SC‑003), (b) alternative covariates if available, (c) robust Huber regression on the full sample. Logs warnings when a check is skipped.  
11. **Visualization** – produces `output/plots/scatter_news_anxiety.png` with scatter of `news_exposure_freq_std` vs. `anxiety_score` and a fitted regression line with 95 % CI.  
12. **Result assembly** – writes `output/results/regression_results.json` adhering to `contracts/output.schema.yaml`; includes `adj_r2_pass` (SC‑002) and `beta_standardized_pass` (SC‑001).  
13. **Causal‑language scan** – validates that generated markdown/text contains only associational phrasing; raises a warning if causal verbs are detected.  
14. **Success‑criteria validation** (`code/validate_sc.py`): inspects the JSON and writes `outputs/success_criteria_log.txt` with PASS/FAIL/BLOCKED for SC‑001 – SC‑005, halting on any failure.  
15. **Documentation** (`code/generate_readme.py`) – creates a reproducible `README.md` summarizing data sources, pipeline steps, runtime, and known limitations (including the current dataset mismatch).  
16. **Archiving** (`code/archive.py`) – zips `code/`, `data/`, and `outputs/` into `archive.zip` for external review.  
17. **Sign‑off** – CI writes `outputs/signoff_report.json` summarizing overall run status (OK / HALTED).  

## Verification Checklist
- `data/raw/` contains the three downloaded parquet files with recorded SHA‑256 checksums **or** a verified survey CSV that satisfies the full schema.  
- `output/results/regression_results.json` exists and is **the sole source of truth**: either `data_status = "HALTED_NO_VALID_DATASET"` with a nested `halt_report` (current state) **or** a full regression result set plus flags. No placeholder numbers appear anywhere.  
- `outputs/success_criteria_log.txt` is generated by executing `code/validate_sc.py` (not hand‑typed).  
- `output/plots/scatter_news_anxiety.png` is produced when a dataset validates.  
- `README.md` is generated by `code/generate_readme.py` and contains a results summary table (when data are available), a clear note about the missing validated anxiety instrument, and reproducibility instructions.  
- `archive.zip` contains the `code/`, `data/processed/`, and `outputs/` directories.  
- Runtime reported in the JSON is ≤ 60 s (SC‑005).  

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| Halt at schema validation | No verified dataset contains required columns (current known state) | Expected behavior per FR‑001. Add a verified open dataset that matches the schema and re‑run. **Do not fabricate data.** |
| N < 30 after cleaning | Excessive missingness in a future valid dataset | Hard stop per FR‑002; cannot proceed. |
| VIF > 10 | Predictor collinearity (e.g., `baseline_anxiety` derived from `anxiety_score`) | Review `vif_scores` in the JSON; the pipeline flags `High VIF` and notes potential collinearity. |
| MCAR test indicates non‑MCAR | Little’s MCAR test returned p < 0.05 | The pipeline adds missingness indicators **and** runs a multiple‑imputation sensitivity analysis; results are still reported with a bias‑warning flag. |
| Robustness skipped | `social_media_engagement` missing or correlation ≤ 0.3 | Review the `flags` array in the JSON; robustness is optional per FR‑006. |
| Proxy instrument unvalidated | Proxy anxiety scale not on whitelist or fails factor‑analysis loading threshold | The pipeline halts with an explicit error (FR‑008). Add a validated proxy or a fully validated instrument. |
| Causal wording appears in README or plots | Causal‑language scan detected prohibited verbs | Revise the generated text to use only associational phrasing; the scan will pass on the next run. |

---


