# Quickstart: Plant Metabolite ↔ Herbivore Resistance Analysis

The quickstart assumes you are on a fresh GitHub Actions runner or a local Linux environment with Python 3.11.

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

The script executes the phases defined in `plan.md` in order:
1. Data acquisition (MetaboLights/PMN/HPID with retry; fallback to placeholder only if all fail).  
2. Pre‑processing & normalization (with documented-absence vs. missing-data distinction).  
3. Power analysis & effective sample-size calculation.  
4. Correlation heatmap generation.  
5. OLS with family covariate & phylogenetic GLS/mixed-effects fitting.  
6. Random Forest training with permutation importance & FDR correction.  
7. Sensitivity analysis (p-threshold sweep, outlier-cap variation, raw-vs-standardized robustness).  
8. Contract validation (processed_data & model_output schemas).  
9. Final report generation with disclaimer (if placeholder was used).

## 3. Inspect results
All artifacts are placed under `outputs/`:

| File | Description |
|------|-------------|
| `clean.parquet` | Normalized dataset ready for downstream analysis; includes optional `absence_indicator` column. |
| `heatmap.png` | Correlation heatmap with significance annotations. |
| `correlation_summary.json` | AnalysisResult: list of metabolite classes with significant negative correlation (q < 0.05). |
| `ols_results.json` | AnalysisResult: OLS coefficients, VIF, family-covariate effect, and performance metrics. |
| `pgls_results.json` | AnalysisResult: phylogenetically adjusted regression output with LRT comparison to OLS. |
| `mixed_effects_results.json` | AnalysisResult: mixed-effects model (family fixed, species random intercept) output. |
| `rf_results.json` | AnalysisResult: feature‑importance ranking (with permutation p-values) + CV performance. |
| `sensitivity.json` | AnalysisResult: results of p‑value‑threshold sweep, outlier‑cap variation, and raw-vs-standardized robustness check. |
| `power_analysis.json` | AnalysisResult: effective sample size, power estimates, and under-power flag. |
| `report.md` | Human‑readable summary linking to all above; includes disclaimer if placeholder data was used. |

## 4. Verify contracts
```bash
# Validate processed data against schema
python -m llmxive_toolkit.validate_contracts \
    --data outputs/clean.parquet \
    --schema contracts/processed_data.schema.yaml

# Validate all result JSONs against model_output schema
for result_file in outputs/*_results.json outputs/power_analysis.json outputs/sensitivity.json; do
  python -m llmxive_toolkit.validate_contracts \
      --data "$result_file" \
      --schema contracts/model_output.schema.yaml
done
```
The commands will raise an error if any output does not conform to the declared schema.

## 5. Re‑run with a different dataset (demo)
If you wish to test the pipeline on the placeholder GHZ dataset directly (for methodology validation only):
```bash
python src/run_pipeline.py \
    --seed 42 \
    --use-placeholder \
    --output-dir outputs_demo/
```
The script will map the placeholder columns to the required schema and proceed through the same analysis steps. **Note**: Results will include a disclaimer that they do not address the biological research question (placeholder is not plant data).

## 6. Interpret the results

### Power & Sample Size
Check `power_analysis.json`:
- If `under_power_flag` is `true`, the study has < 50 species after filtering and is exploratory.
- If `effective_n` is substantially less than `observed_n`, phylogenetic adjustment has reduced the independent information; interpret accordingly.

### Biomarker Identification
Check `correlation_summary.json` and `rf_results.json`:
- Metabolites with q < 0.05 (FDR-corrected) in both OLS and Random Forest are robust candidates.
- Compare `pgls_results.json` to `ols_results.json`: if LRT p < 0.05, phylogenetic adjustment significantly improves fit.
- Check `sensitivity.json` for robustness: if biomarker rankings are consistent across p-thresholds and raw-vs-standardized analyses, confidence is higher.

### Data Source
Check `report.md` for a disclaimer:
- If results are based on MetaboLights/PMN/HPID data, conclusions address the biological research question.
- If results are based on placeholder data, they validate the pipeline methodology only.

---