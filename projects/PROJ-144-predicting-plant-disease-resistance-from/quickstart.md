# Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:
- Python 3.8 or higher installed
- pip package manager
- Internet access for downloading data from Metabolomics Workbench
- At least 8GB RAM available
- ~2GB free disk space for intermediate files

## Step-by-Step Execution

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate # Linux/Mac
# or
venv\\Scripts\\activate # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Study Availability

```bash
python code/research/verify_studies.py
```

**Expected Output**:
- `data/raw/study_manifest.json` created
- Console message showing number of valid studies found

**Validation**:
```bash
cat data/raw/study_manifest.json | python -m json.tool
```

### 3. Download Raw Data

```bash
python code/data/download_study.py --study_ids data/raw/study_manifest.json
```

**Expected Output**:
- Raw CSV files in `data/raw/`
- Checksum files generated
- Temporal verification completed

**Validation**:
```bash
ls -lh data/raw/
```

### 4. Preprocess Data

```bash
python code/data/preprocess.py --study_ids data/raw/study_manifest.json --output data/processed/
```

**Expected Output**:
- `data/processed/batch_corrected_matrix.csv`
- `data/processed/labels.csv`
- `data/processed/preprocess_log.json`

**Validation**:
```bash
head -5 data/processed/batch_corrected_matrix.csv
wc -l data/processed/batch_corrected_matrix.csv
```

### 5. Train Model

```bash
python code/modeling/train.py --input data/processed/ --output results/
```

**Expected Output**:
- Trained model saved
- `results/feature_importance_ranking.json`
- Cross-validation results

**Validation**:
```bash
cat results/feature_importance_ranking.json | python -m json.tool
```

### 6. Evaluate Model

```bash
python code/modeling/evaluate.py --input data/processed/ --results results/
```

**Expected Output**:
- `results/metrics.json`
- `results/shap_analysis.json`
- Learning curve plots

**Validation**:
```bash
cat results/metrics.json | python -m json.tool
```

### 7. Interpret Results

```bash
python code/modeling/interpret.py --results results/
python code/modeling/generate_final_metrics.py --results results/
```

**Expected Output**:
- `results/pathway_analysis.json`
- `results/top_metabolites.json`
- Visualization plots in `results/plots/`

**Validation**:
```bash
ls -lh results/plots/
cat results/pathway_analysis.json | python -m json.tool
```

### 8. Generate Final Report

```bash
python code/modeling/generate_associational_report.py --results results/
```

**Expected Output**:
- `results/report_framing.md`
- Consolidated associational report

**Validation**:
```bash
grep -i "associations" results/report_framing.md
```

## Common Issues

### Issue: "Study not found" error
**Solution**: Ensure the Metabolomics Workbench API is accessible and the study IDs in `study_manifest.json` are valid.

### Issue: "Insufficient memory" error
**Solution**: Reduce the number of studies processed or increase available RAM. The pipeline will automatically switch to streaming mode for large datasets.

### Issue: "Temporal verification failed"
**Solution**: This is expected if a study lacks pre-challenge/baseline samples. The pipeline will skip that study and log a warning.

### Issue: "ComBat not applicable"
**Solution**: This warning appears when only one study is present. Batch correction is correctly skipped in this case.

## Verification Checklist

After running the full pipeline, verify:

- [ ] `data/raw/study_manifest.json` exists and is valid JSON
- [ ] `data/processed/batch_corrected_matrix.csv` exists with >10 metabolites
- [ ] `data/processed/labels.csv` exists with binary labels
- [ ] `results/metrics.json` contains balanced_accuracy, roc_auc, permutation_p_value
- [ ] `results/shap_analysis.json` contains correlation data and framing
- [ ] `results/pathway_analysis.json` contains pathway mappings and narrative
- [ ] `results/plots/` contains at least one PNG file
- [ ] All JSON files contain the "framing" field with associational text
- [ ] `state/artifact_hashes.yaml` contains SHA256 checksums for all artifacts

## Next Steps

1. Review the generated reports in `results/`
2. Examine the pathway analysis for biological plausibility
3. Validate the associational framing in all outputs
4. Consider extending the analysis with additional datasets
5. Share findings with appropriate caveats about associational nature

## Support

For issues or questions, refer to the full documentation in `README.md` or check the test suite in `tests/` for usage examples.