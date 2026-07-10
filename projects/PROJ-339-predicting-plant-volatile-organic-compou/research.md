# Research Status: Predicting Plant VOC Emission Profiles

## Overview

This project aims to predict plant volatile organic compound (VOC) emission profiles
using genomic data (RNA-seq) and environmental metadata. The approach utilizes a
Random Forest Regressor with Nested Cross-Validation to ensure robust performance
metrics (R², RMSE) while avoiding overfitting.

## Data Availability Status

### Real Data Sources

The primary data sources for this research are:
1. **NCBI Gene Expression Omnibus (GEO)**: For RNA-seq data under stress conditions.
2. **Metabolomics Workbench**: For VOC profiling data.

**Current Status**: As of the latest query (see `data/raw/query_log.json`),
finding *exact* paired samples (same biological replicate, same time point) for
both RNA-seq and VOC measurements in *Arabidopsis thaliana* under specific stress
conditions remains a significant challenge. Public datasets often lack the necessary
granularity or pairing metadata.

**Action Taken**: The pipeline currently defaults to the **Synthetic Data Generator**
(`code/generators/synthetic_data.py`) to validate the end-to-end workflow. This
synthetic data mimics the statistical properties of real *Arabidopsis* stress responses
(e.g., upregulation of Terpene Synthase families under heat/drought) but does not
represent specific experimental measurements.

**Next Steps for Real Data**:
- Manual curation of specific GEO series (e.g., GSEXXXXX) that include metabolomics.
- Collaboration with labs holding raw paired datasets.
- Refinement of search queries in `code/00_query_sources.py` to include broader
 stress conditions or related species.

## Methodology

1. **Ingestion**: Data is loaded and normalized to TPM (Transcripts Per Million) for
 gene expression. Environmental variables (temperature, light intensity) are parsed.
2. **Preprocessing**:
 - **Replicate Filtering**: Conditions with <3 biological replicates are excluded.
 - **Environmental Filtering**: Samples missing continuous environmental metadata
 are excluded to ensure model robustness.
 - **Imputation**: Median imputation is applied to non-critical missing fields.
3. **Feature Engineering**: Gene expression is aggregated into pathway-level features
 (e.g., TPS gene families) to reduce dimensionality and improve biological interpretability.
4. **Modeling**:
 - **Algorithm**: Random Forest Regressor.
 - **Validation**: Nested k-Fold Cross-Validation (5 outer, 3 inner folds).
 - **Hardware**: CPU-only execution.
5. **Interpretation**:
 - **Permutation Importance**: To rank feature contributions.
 - **SHAP Values**: For local and global explanation of predictions.
 - **Biological Validation**: Overlap analysis against known Terpene Synthase families.

## Results Summary

*Note: Results below reflect the synthetic data run.*

- **Model Performance**: R² and RMSE metrics are recorded in `data/results/model_metrics.json`.
- **Key Features**: Top predictors include TPS04, TPS06, and specific environmental
 interaction terms (e.g., Temperature × Light).
- **Stability**: Feature importance rankings show moderate stability across CV folds
 (see `data/results/stability_metrics.json`).

## Limitations

- **Observational Nature**: Findings are associational; causal inference is not possible
 without controlled experimental intervention.
- **Data Scarcity**: The reliance on synthetic data for the current run limits the
 generalizability of the specific performance metrics to real-world scenarios.
- **Environmental Complexity**: The model currently accounts for temperature and light
 but may miss other critical factors (humidity, soil nutrients) if not present in the input.

## Future Work

- **Data Acquisition**: Secure access to real paired datasets.
- **Model Expansion**: Explore Gradient Boosting or Neural Networks for non-linear interactions.
- **Temporal Dynamics**: Incorporate time-series modeling if longitudinal data becomes available.