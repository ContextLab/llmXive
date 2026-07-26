# Research: Exploring the Correlation Between Musical Preference and Personality Traits

## Decision / Rationale
- **Data Strategy** – The specification requests the OpenML BFI‑2 dataset and a Last.fm listening archive. **No openly downloadable, programmatically accessible dataset that contains both personality scores *and* listening behavior exists at present**. Consequently the pipeline **first attempts** to download those sources. If either download fails (as on the CI runner), a **deterministic synthetic dataset** (seed = 42) is generated to **validate the full analysis workflow**. The synthetic data are realistic but **cannot substantiate real‑world claims**; they are used solely for pipeline verification. When an appropriate open dataset becomes available, the same pipeline will be re‑run to answer the substantive research question.

- **Computation Strategy** – All analyses use CPU‑only libraries (`pandas`, `scipy`, `statsmodels`). No GPU is required, keeping the workflow within the GitHub Actions free‑tier limits.

## Dataset Strategy

| Need | Proposed Source | Access Method | Notes |
|------|----------------|---------------|-------|
| Personality scores (BFI‑2) | **Synthetic generator** (`code/generate_synthetic.py`) | Local generation, reproducible with seed 42 | No verified external source; synthetic scores follow the BFI‑2 1‑5 Likert range. |
| Listening behavior (Last.fm) | **Synthetic generator** (`code/generate_synthetic.py`) | Local generation | Generates log‑normal listening minutes across the 10 standardized genres plus “Other”. |
| Demographics (age, gender, country, education, SES, total listening minutes) | **Synthetic generator** (`code/generate_synthetic.py`) | Local generation | Age range encompassing the adult population (uniform), gender balanced, country codes with rare values collapsed to “Other”, education levels, SES categories, total minutes derived from genre sums. |

> **Limitation:** Results derived from the synthetic data are illustrative of pipeline correctness only. Real‑world inference requires an open dataset that satisfies the above columns; the plan will automatically re‑run on such a dataset when provided.

## Methodological Details

| Method | Description | Deferred Values |
|--------|-------------|-----------------|
| **Spearman rank correlation** | Compute ρ and two‑tailed p‑value for each of the examined traits × 10 genres (log‑transformed minutes). | `ρ`, `p` |
| **Log‑transformation** | `log1p(listening_minutes)` to reduce skew. | — |
| **Multiple linear regression** | Trait ~ genre_score + age + gender + country + education + SES + total_listening_minutes (one‑hot for categoricals). | β, SE, p |
| **Bonferroni correction** | Adjust p‑values for 5 × 10 = 50 tests; α = 0.001. | adjusted p |
| **Effect size** | Cohen’s d derived from Spearman ρ: `d = 2ρ / sqrt(1‑ρ²)`. | d |
| **Confidence intervals** | 95 % CI for d via Fisher’s z‑transformation of ρ. | CI lower/upper |
| **Collinearity check** | Compute VIF for each predictor; drop any with VIF > 5, log warning. | — |
| **Sensitivity analysis** | Re‑run significance testing at α = 0.01, 0.005, 0.001 to assess stability. | — |
| **Power analysis** | Sample size calculation for detecting |ρ| ≈ 0.3 with 80 % power at α = 0.001 (two‑tailed). | Sample size ≈ a few k (synthetic set uses a larger scale). |

All statistical steps are scripted in `code/analysis.py` and logged.

## Expected Deliverables
- `data/processed/merged_dataset.csv` – cleaned, merged synthetic (or real) data.  
- `data/processed/analysis_results.csv` – table with all FR‑003/FR‑004 outputs plus flags, conforming to `contracts/analysis_results.schema.yaml`.  
- `data/processed/coefficient_deltas.csv` – regression coefficient deltas and related metrics, conforming to `contracts/analysis_output.schema.yaml`.  
- `results/correlation_heatmap.png` – heatmap of Spearman ρ values.  
- `results/results_report.csv` – CSV with Cohen’s d, 95 % CIs, significance labels, `high_correlation_flag`, conforming to `contracts/report.schema.yaml`.  
- `logs/` – detailed execution logs, including any dropped covariates, fallback decisions, and power‑analysis summary.
