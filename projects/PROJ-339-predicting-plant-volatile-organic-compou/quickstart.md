# Quickstart Guide

This guide provides instructions for setting up the environment and running the full
predictive modeling pipeline for Plant VOC Emission Profiles.

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- Git

## 1. Environment Setup

### Clone and Install Dependencies

```bash
git clone <repository-url>
cd <project-directory>
pip install -r requirements.txt
```

### Configure Environment Variables

Copy the example environment file and update paths/seeds as needed:

```bash
cp.env.example.env
# Edit.env to set DATA_ROOT, SEED, etc.
```

## 2. Generate Synthetic Data (for testing/demos)

Since real paired RNA-seq and VOC data for *Arabidopsis thaliana* under stress
conditions is scarce and requires manual curation from NCBI GEO and Metabolomics Workbench,
we provide a canonical synthetic data generator for pipeline validation.

**Command to generate synthetic data:**

```bash
python code/generators/synthetic_data.py
```

This script produces:
- `data/raw/synthetic_arabidopsis_v1.csv` (Synthetic paired genomic and VOC data)
- `data/raw/query_log.json` (Log indicating synthetic fallback was used)

*Note: For production runs, replace the synthetic data step with the real data query
script `code/00_query_sources.py` once real data sources are populated.*

## 3. Run the Full Pipeline

The pipeline consists of sequential stages. Run them in order:

```bash
# Stage 1: Ingest and Normalize
python code/01_ingest.py

# Stage 2: Merge Data (filtering replicates and environmental metadata)
python code/02_merge.py

# Stage 3: Aggregate Genes to Pathways
python code/03_aggregate.py

# Stage 4: Train Model (Nested CV)
python code/03_train.py

# Stage 5: Interpret Model (SHAP, Permutation Importance)
python code/04_interpret.py

# Stage 6: Overlap Analysis (Biological validation)
python code/05_overlap_analysis.py

# Stage 7: Validate Stability
python code/05_validate_stability.py

# Stage 8: Generate Final Report
python code/06_generate_report.py
```

## 4. Output Artifacts

Upon successful completion, the following artifacts will be available:

- **Processed Data**: `data/processed/merged_dataset.csv`
- **Model**: `data/models/random_forest.pkl`
- **Metrics**: `data/results/model_metrics.json`
- **Interpretation**: `data/results/interpretation_report.json`, `data/results/shap_summary.png`
- **Validation**: `data/results/data_validation_report.json`, `data/results/stability_metrics.json`

## 5. Validation

To verify the pipeline execution and data integrity:

```bash
python code/05_validate.py
```

This checks for numeric consistency, missing values, and schema compliance.

## Troubleshooting

- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Data Path Errors**: Verify `.env` file configuration.
- **Memory Issues**: The pipeline is optimized for CPU; reduce dataset size if OOM occurs.
