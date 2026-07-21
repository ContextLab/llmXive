# Quick Start Guide

This guide provides step-by-step instructions to validate the plant disease resistance prediction pipeline.

## Prerequisites Check

Before running the pipeline, ensure you have:

```bash
# Python version
python --version # Should be 3.11 or higher

# Required packages
pip list | grep -E "pandas|numpy|scikit-learn|statsmodels|shap|biopython|requests|pytest|pyyaml"
```

## Step 1: Verify Project Structure

Ensure all required directories exist:

```bash
# Check directory structure
ls -la code/ data/ tests/ results/ state/ contracts/
```

Expected directories:
- `code/` - Source code
- `data/raw/` - Raw downloaded data
- `data/processed/` - Preprocessed data
- `tests/` - Test suite
- `results/` - Analysis outputs
- `state/` - Pipeline state tracking
- `contracts/` - Data schemas

## Step 2: Data Acquisition Validation

### Download Raw Data

```bash
python code/data/download.py
```

**Expected Output:**
- Files downloaded to `data/raw/`
- Log messages confirming successful downloads
- At least 2 studies downloaded (check `data/raw/` for study folders)

**Validation:**
```bash
# Check downloaded files
ls -la data/raw/
# Verify file integrity (checksums logged to state/)
cat state/artifact_hashes.yaml
```

### Validate Temporal Consistency

```bash
python code/data/validate_temporal.py
```

**Expected Output:**
- No temporal violations (all `sample_time < challenge_time`)
- If violations exist, the script will exit with an error

### Harmonize Labels

```bash
python code/data/harmonize_labels.py
```

**Expected Output:**
- Labels encoded as binary/ordinal
- Z-scoring or stratification applied
- Output saved to `data/processed/labels.csv`

### Preprocess Data

```bash
python code/data/preprocess.py
```

**Expected Output:**
- Log-transformed intensities
- Features with >30% missing values discarded
- Metabolites aligned via InChIKey
- Covariate residualization performed
- ComBat batch-effect correction applied (if ≥2 studies)

### Generate Processed Outputs

```bash
python code/data/generate_processed_outputs.py
```

**Expected Output:**
- `data/processed/batch_corrected_matrix.csv` created
- `data/processed/labels.csv` created
- Both files non-empty and properly formatted

**Validation:**
```bash
# Check file sizes
ls -lh data/processed/
# Verify CSV structure
head -n 5 data/processed/batch_corrected_matrix.csv
head -n 5 data/processed/labels.csv
```

## Step 3: Model Training and Validation

### Train Model

```bash
python code/modeling/train.py
```

**Expected Output:**
- 20% hold-out set reserved before feature selection
- Random Forest trained with 5-fold stratified CV
- GridSearchCV performed for hyperparameter tuning
- Model saved to `state/`

### Evaluate Model

```bash
python code/modeling/evaluate.py
```

**Expected Output:**
- Balanced Accuracy, ROC-AUC, Precision-Recall computed on hold-out set
- Permutation testing (≥1,000 permutations) completed
- Benjamini-Hochberg FDR correction applied
- Sensitivity analysis performed
- Learning curve generated
- Results saved to `results/metrics.json`

**Validation:**
```bash
# Check metrics file
cat results/metrics.json
# Verify balanced accuracy > 0.75 (hypothesis threshold)
python -c "import json; m=json.load(open('results/metrics.json')); print('Balanced Acc:', m.get('balanced_accuracy'))"
```

### Collinearity Diagnostics

```bash
python code/modeling/collinearity.py
```

**Expected Output:**
- VIF calculated for selected metabolites
- Metabolites with VIF > 5 flagged
- Results logged

### Generate Associational Report

```bash
python code/modeling/generate_associational_report.py
```

**Expected Output:**
- `results/associational_report.md` created
- All findings framed as **ASSOCIATIONAL** (not causal)

## Step 4: Biological Interpretation

### Interpret Model

```bash
python code/modeling/interpret.py
```

**Expected Output:**
- Top metabolites by SHAP values extracted
- Pathway mapping via KEGG/MetaCyc
- Biological plausibility discussion generated

### Save Pathway Results

```bash
python code/modeling/save_pathway_results.py
```

**Expected Output:**
- `results/pathway_analysis.json` created
- Top 10 metabolites mapped to pathways

### Visualize Pathways

```bash
python code/modeling/visualize_pathways.py
```

**Expected Output:**
- `results/pathway_barplot.png` generated
- Visualization shows top pathways and feature importances

**Validation:**
```bash
# Check pathway analysis file
cat results/pathway_analysis.json
# Verify plot exists
ls -lh results/pathway_barplot.png
```

## Step 5: Full Integration Test

Run the complete pipeline end-to-end:

```bash
# Execute all stages in sequence
bash scripts/run_full_pipeline.sh # If available, or run each script manually
```

**Expected Outcome:**
- All scripts complete without errors
- All output files generated
- `state/artifact_hashes.yaml` updated with all artifact checksums

## Step 6: Unit and Integration Tests

```bash
# Run all tests
pytest -v

# Run specific test suites
pytest tests/unit/ -v
pytest tests/integration/ -v
```

**Expected Outcome:**
- All tests pass
- No failures or errors

## Common Issues and Troubleshooting

### Data Download Fails

- **Cause**: No internet connection or Metabolomics Workbench unavailable
- **Solution**: Check network connection, verify study IDs in `research.md`

### Missing Dependencies

- **Cause**: Required packages not installed
- **Solution**: Run `pip install -r requirements.txt`

### Memory Errors

- **Cause**: Dataset too large for available RAM
- **Solution**: Use streaming mode or process in chunks (see `code/data/preprocess.py`)

### Temporal Validation Fails

- **Cause**: Sample time > challenge time in metadata
- **Solution**: Review and correct metadata in source files

## Validation Checklist

Use this checklist to confirm all components are working:

- [ ] Project structure verified
- [ ] Data downloaded (≥2 studies)
- [ ] Temporal validation passed
- [ ] Labels harmonized
- [ ] Data preprocessed (log-transformed, batch-corrected)
- [ ] Processed outputs generated (`batch_corrected_matrix.csv`, `labels.csv`)
- [ ] Model trained with CV and hold-out set
- [ ] Metrics computed (Balanced Acc, ROC-AUC, etc.)
- [ ] Permutation testing completed (≥1,000 permutations)
- [ ] FDR correction applied
- [ ] Collinearity diagnostics performed (VIF calculation)
- [ ] Associational report generated (findings framed as associational)
- [ ] SHAP analysis completed
- [ ] Pathway mapping performed (top 10 metabolites)
- [ ] Pathway visualization generated
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] `state/artifact_hashes.yaml` contains all artifact checksums

## Next Steps

After successful validation:

1. Review `results/associational_report.md` for key findings
2. Examine `results/pathway_barplot.png` for biological insights
3. Check `results/metrics.json` for model performance
4. Update `research.md` with actual dataset citations and power analysis
5. Deploy to production or continue with further analysis

## Resources

- [Metabolomics Workbench](https://www.metabolomicsworkbench.org/)
- [KEGG Pathway Database](https://www.kegg.jp/)
- [MetaCyc Pathway Database](https://metacyc.org/)
- [SHAP Documentation](https://shap.readthedocs.io/)
- [scikit-learn Documentation](https://scikit-learn.org/)