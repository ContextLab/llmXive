# Quickstart: Investigating Circadian Gene Expression & Metabolic Syndrome Risk

This guide describes how to execute the exploratory pipeline on a CPU‑only environment.

## Prerequisites
- Python 3.11
- 2 CPU cores, ≥ 6 GB RAM
- Internet access for verified HuggingFace datasets (when URLs become available)

## Setup
```bash
git clone https://github.com/your-org/circadian-metabolic-correlation.git
cd circadian-metabolic-correlation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Pipeline
The pipeline is executed via a single entry point. It will automatically perform the CPU‑only check and then proceed through data acquisition and analysis.

```bash
# Execute the full pipeline
python src/pipelines/run_pipeline.py --seed 42
```

### Pipeline Steps:
1. **T060 CPU Check**: Runs `src/scripts/cpu_check.py` to ensure no GPU is present.  
   *Note*: In the CI environment a GitHub Actions workflow (see CI Enforcement section) will invoke this script as a blocking step.
2. **Phenotype & Expression Load**: Attempts to fetch a **single open dataset** that provides both TPM matrices and the five ATP‑III clinical variables. If such a dataset is not yet available, the pipeline logs a warning and proceeds in exploratory mode using GTEx expression only.  
3. **MetS Binary Classification (FR‑002)**: For donors with complete ATP‑III data, apply ATP‑III thresholds (≥ 3 criteria) → `MetS` or `Control`. Donors missing any variable are excluded from binary analyses. Output written to `classification.csv`.  
4. **PMI Residualization (FR‑031)**: Fit `TPM ~ PMI` per gene‑tissue and replace TPM with residuals.  
5. **Statistical Analysis**: 
   - ANCOVA (with hierarchical pooling fallback) comparing gene expression between MetS and Control groups (FR‑003, FR‑013, FR‑020).  
   - Mixed‑effects linear models for gene‑trait correlations (FR‑007, FR‑014).  
   - Univariate logistic odds ratios for metabolic traits (FR‑009).  
   - Batch‑effect sensitivity analysis (FR‑015).  
   - Multivariate logistic regression with 5‑fold CV **if** ≥ 100 donors have binary labels (FR‑005, FR‑006).  
6. **Correction**: Applies global Benjamini‑Hochberg FDR.  
7. **Validation**: Validates all resulting CSVs against the schemas in `contracts/`.  
   *External validation on MESA is skipped until a verified dataset is available (FR‑010).*
8. **Diagnostics & Figures**: Generates heatmaps, ROC curves (when applicable), and scatter plots for significant findings.  

## Expected Outputs
- `data/processed/de_results.csv`: ANCOVA coefficients and adjusted p‑values for core circadian genes.  
- `data/processed/correlation_results.csv`: Gene‑trait correlation coefficients and significance.  
- `data/processed/univariate_logistic_results.csv`: Odds ratios for each metabolic trait.  
- `data/processed/batch_sensitivity.csv`: Coefficient stability metrics.  
- `data/processed/success_metrics.csv`: Consolidated SC metrics.  
- Figures in `src/results/figures/`: Heatmaps, ROC curves (when applicable), and scatter plots.
