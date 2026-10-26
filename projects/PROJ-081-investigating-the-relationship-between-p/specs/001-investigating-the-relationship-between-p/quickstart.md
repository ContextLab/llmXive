# Quickstart: Plant Metabolite ↔ Herbivore Resistance Analysis

The quickstart works on a fresh GitHub Actions runner or any Linux environment with Python 3.11.

## 1. Clone the repository & install dependencies
```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 2. Run the full pipeline
```bash
python src/run_pipeline.py \
    --seed 42 \
    --max-species 100 \
    --output-dir outputs/
```
- `--seed` fixes all randomness.  
- `--max-species` caps the number of species processed (useful for very large downloads).  

The script executes the phases defined in **plan.md** in order:

1. **Data acquisition** – attempts MetaboLights, PMN, HPID; on total failure falls back to the **GHZ placeholder dataset** (`https://huggingface.co/datasets/khaoula-ghz/guanaco-llama2-5k/resolve/main/data/train-00000-of-00001.parquet`). The placeholder **does not contain real plant metabolite or herbivory measurements**; a disclaimer is added to the final report.  
2. **Pre‑processing** – handles documented absences via `absence_indicator`, performs outlier capping, **imputes missing values on the raw scale**, then **z‑score standardization**.  
3. **Correlation** – computes both class‑level and compound‑level Pearson correlations; generates `outputs/heatmap.png`. Results are for exploratory reporting only; **all metabolites are retained for downstream modeling**.  
4. **Train‑test split** – reserves 20 % of species as a hold‑out set for unbiased evaluation.  
5. **Baseline OLS** – fits OLS on the training set with family covariate; computes VIF diagnostics.  
6. **Phylogenetic GLS & Mixed‑effects** – PGLS using Open Tree of Life covariance; mixed‑effects with species random intercept.  
7. **Random Forest** – shallow RF (`max_depth=5`, 200 trees) with 5‑fold CV; reports **permutation importance rankings** (no p‑values).  
8. **Sensitivity analysis** – p‑value‑threshold sweep, outlier‑cap variation, raw vs. standardized comparison.  
9. **Power analysis** – computes effective α = 0.05 / total_tests and uses a conservative target effect size (r≈0.2).  
10. **Reporting** – generates `outputs/report.md` with a disclaimer that the placeholder data are not biologically meaningful and that FR‑001 could not be satisfied.

## 3. Inspect results
All artifacts are under `outputs/`:

| File | Description |
|------|-------------|
| `clean.parquet` | Normalized dataset; no missing values; includes optional `absence_indicator`. |
| `heatmap.png` | Correlation heatmap with significance annotations. |
| `correlation_summary.json` | List of metabolite classes with significant negative correlation (q < 0.05). |
| `ols_results.json` | OLS coefficients, VIF, performance metrics. |
| `pgls_results.json` | Phylogenetic GLS output + LRT vs OLS. |
| `mixed_effects_results.json` | Mixed‑effects model output (family fixed, species random). |
| `rf_results.json` | Permutation **importance rankings** (no p‑values) + CV / test performance. |
| `sensitivity.json` | Results of p‑threshold sweep, outlier‑cap variation, raw‑vs‑standardized robustness. |
| `power_analysis.json` | Effective sample size, power estimates, under‑power flag. |
| `report.md` | Human‑readable summary linking to all artifacts; contains disclaimer if placeholder data were used. |

## 4. Validate contracts
```bash
# Validate processed data
python -m llmxive_toolkit.validate_contracts \
    --data outputs/clean.parquet \
    --schema contracts/processed_data.schema.yaml

# Validate all JSON result files
for f in outputs/*_results.json outputs/power_analysis.json outputs/sensitivity.json; do
  python -m llmxive_toolkit.validate_contracts \
      --data "$f" \
      --schema contracts/model_output.schema.yaml
done
```
Any validation error aborts the run, guaranteeing deterministic, verifiable artifacts.

## 5. Run with placeholder data only (methodology demo)
```bash
python src/run_pipeline.py \
    --seed 42 \
    --use-placeholder \
    --output-dir outputs_demo/
```
The placeholder GHZ dataset is loaded from the verified URL above, mapped to the required schema, and processed through the same pipeline. **A disclaimer will be added to `outputs_demo/report.md`** stating that the data are not plant metabolite and herbivory measurements; results are methodological only.

## 6. Interpreting the outputs

### Power & Sample Size (`power_analysis.json`)
- `under_power_flag: true` → < 50 species after filtering; treat results as exploratory.  
- `effective_n` indicates the phylogenetically adjusted sample size.

### Biomarker Identification
- **Correlation**: Check `correlation_summary.json` for classes with q < 0.05 (negative direction).  
- **Regression**: In `ols_results.json`, metabolites with q < 0.05 and VIF < 5 are strong candidates.  
- **Random Forest**: `rf_results.json` ranks metabolites by permutation importance; **no p‑values** are provided.  
- **Phylogenetic check**: Compare coefficients & significance between OLS and PGLS (`pgls_results.json`). A significant LRT (p < 0.05) indicates phylogenetic non‑independence matters.  

### Robustness
- Review `sensitivity.json`: stable rankings across q‑threshold sweeps and raw vs. standardized analyses increase confidence.

### Data Source
- Open `report.md` – it explicitly states whether the analysis used real MetaboLights/PMN/HPID data or the GHZ placeholder. If the latter, the report is a pipeline proof‑of‑concept only. 

---
