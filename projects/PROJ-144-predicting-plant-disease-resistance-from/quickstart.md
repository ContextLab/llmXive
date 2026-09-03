# Quickstart Guide: Predicting Plant Disease Resistance from Metabolomic Data

This guide provides the exact commands to run the full pipeline end-to-end.

## Prerequisites

- Python 3.9+
- pip
- Internet access (for downloading datasets and KEGG API calls)

## Installation

```bash
# Install dependencies
pip install -r code/requirements.txt
```

## Full Pipeline Execution

Run the following commands in order to execute the entire pipeline:

### Phase 0: Data Acquisition

```bash
# 1. Discover plant metabolomics studies
python code/data/discover_studies.py --output data/raw/study_manifest_raw.json

# 2. Serialize study manifest
python code/data/serialize_manifest.py --input data/raw/study_manifest_raw.json --output data/raw/study_manifest.json

# 3. Validate study manifest
python code/data/validate_manifest.py --input data/raw/study_manifest.json --schema contracts/metadata.schema.yaml --output state/schema_validation_log.txt

# 4. Download raw data for all studies
python code/data/download_study.py --manifest data/raw/study_manifest.json --output-dir data/raw

# 5. Match resistance metadata and filter studies
python code/data/match_and_download.py --input data/raw --output data/raw/filtered_study_manifest.json

# 6. Validate temporal metadata
python code/data/validate_temporal.py --input data/raw --output data/processed/temporal_validation_log.json

# 7. Detect label heterogeneity
python code/data/detect_label_heterogeneity.py --input data/raw --output data/processed/heterogeneity_report.json
```

### Phase 1: Preprocessing

```bash
# 8. Harmonize labels
python code/data/harmonize_labels.py --input data/raw --heterogeneity data/processed/heterogeneity_report.json --output data/processed/harmonized_labels.csv

# 9. Execute preprocessing pipeline (log transform, filter, align, ComBat)
python code/data/preprocess.py --input data/raw --output data/processed
```

### Phase 2: Modeling

```bash
# 10. Split data (or configure learning curve if N < 50)
python code/modeling/split_data.py --input data/processed --output data/processed/split_config.json

# 11. Train model
python code/modeling/train.py --input data/processed --output results/model.pkl

# 12. Extract feature importance
python code/modeling/extract_feature_importance.py --input results/model.pkl --output results/feature_importance_ranking.json

# 13. Correlation analysis with FDR
python code/modeling/correlation_analysis.py --input data/processed --output results/correlation_analysis_fdr_corrected.json

# 14. Model validation and permutation testing
python code/modeling/validate_model.py --input data/processed --model results/model.pkl --output results/model_validation.json

# 15. Sensitivity analysis
python code/modeling/sensitivity_analysis.py --input data/processed --model results/model.pkl --output results/sensitivity_analysis.json

# 16. Collinearity diagnostics
python code/modeling/collinearity.py --input data/processed --output results/vif_scores.json
```

### Phase 3: Interpretation (T043 - KEGG API with Retry/Fallback)

```bash
# 17. Extract top metabolites
python code/modeling/extract_feature_importance.py --input results/model.pkl --output results/top_metabolites.json

# 18. Map pathways with KEGG API (includes retry/fallback logic)
python code/modeling/interpret.py --input results/top_metabolites.json --output results/pathway_analysis.json

# 19. Generate pathway report
python code/modeling/generate_framing_report.py --input results/pathway_analysis.json --output results/pathway_report.json

# 20. Merge pathway analysis
python code/modeling/merge_pathway_analysis.py --input results --output results/pathway_analysis.json
```

### Phase 4: Final Report

```bash
# 21. Generate final metrics and summary
python code/modeling/generate_final_metrics.py --input results --output results/analysis_summary.json

# 22. Generate associational report
python code/modeling/generate_associational_report.py --input results/analysis_summary.json --output results/report_framing.md
```

## Verification

After running the pipeline, verify that all expected outputs exist:

```bash
# Check key artifacts
ls -lh data/raw/study_manifest.json
ls -lh data/processed/heterogeneity_report.json
ls -lh data/processed/temporal_validation_log.json
ls -lh results/pathway_analysis.json
ls -lh results/analysis_summary.json
```

## Troubleshooting

- **KEGG API timeouts**: The `interpret.py` script automatically retries with exponential backoff. If failures persist, check your internet connection.
- **Missing data files**: Ensure all previous steps completed successfully. Check `data/raw/` and `data/processed/` directories.
- **Class imbalance**: If you see `ClassImbalanceError`, check the distribution of your labels in the hold-out set.

## Limitations

These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made.