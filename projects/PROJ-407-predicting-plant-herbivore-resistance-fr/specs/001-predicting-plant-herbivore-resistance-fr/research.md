# Research: Predicting Plant Herbivore Resistance from Publicly Available Metabolomic Data

## Executive Summary

This research validates the feasibility of predicting plant herbivore resistance using publicly available metabolomic data. The core hypothesis is that metabolite abundance profiles contain non-random signals correlating with resistance scores (e.g., leaf area loss). The proposed methodology prioritizes CPU-tractability, statistical rigor (permutation testing, multiple-testing correction), and strict adherence to data availability constraints.

## Dataset Strategy

### Verified Datasets
Per the project constraints, we rely exclusively on the following verified sources.

| Dataset Name | Verified URL | Format | Usage |
|:--- |:--- |:--- |:--- |
| Plant Metabolomics Herbivore Resistance | `https://huggingface.co/datasets/plant-metabolomics/herbivore-resistance-v1` | Parquet | **Primary**: Contains paired metabolite profiles and quantifiable resistance scores. Loaded via `datasets.load_dataset("plant-metabolomics/herbivore-resistance-v1")`. |
| NCBI Disease (Mock) | ` | ZIP | **Fallback**: Only if primary dataset is inaccessible. *Not* the primary scientific target. |

**Critical Data Availability Note**:
The spec previously mentioned `GSE12345`, but this accession is **not** in the verified block.
* **Strategy**: The implementation will fetch `plant-metabolomics/herbivore-resistance-v1` directly via the HuggingFace `datasets` library.
* **If Real Download Fails**: The pipeline will abort with a clear error: "No verified metabolomic dataset found. Aborting."
* **No Synthetic Data**: We will **not** fabricate a metabolomic dataset. The pipeline is designed to fail gracefully if the specific biological data is unavailable, adhering to the "Public-Dataset Provenance" principle.

### Dataset Variable Fit
* **Required Variables**: `sample_id`, `genotype_id`, `metabolite_abundances` (multiple columns), `resistance_score` (numeric or ordinal).
* **Fit Check**: The ingestion script (`code/ingest.py`) will perform a schema validation immediately after download.
 * **Continuous vs. Binary**: If `resistance_score` is binary (e.g., "Infested"/"Control"), the pipeline switches to Classification (Accuracy/AUC) instead of Regression (R²). If the scientific question strictly requires a continuous score and only binary data exists, the pipeline aborts.
* **Gap**: If the selected dataset lacks specific covariates (e.g., herbivore density), the system flags this limitation (FR-008) but proceeds if the primary outcome exists.

## Methodological Rigor

### Statistical Approach
1. **Model**: Random Forest Regressor (or Classifier if target is binary/ordinal).
 * *Rationale*: Handles non-linear relationships, robust to outliers, provides feature importance. CPU-tractable for ≤500 samples.
2. **Split Strategy**: **Genotype-Held-Out**. All samples of a specific genotype are either in the training set or the test set, never both. This prevents leakage due to genetic background similarity.
3. **Validation**:
 * **Permutation Testing (a sufficient number of iterations)**: To establish a null distribution of R² scores. **Stratified by genotype** to maintain the correlation structure within genotypes. This addresses **SC-001** and **FR-005**.
 * **Multiplicity Correction**: Benjamini-Hochberg (BH) procedure on univariate correlation p-values. Addresses **SC-002** and **FR-006**.
 * **Conditional Reporting**: The univariate correlation analysis and BH correction are **only** performed if the global permutation test yields p < 0.05. This prevents "double-dipping" on noise.
 * **Batch Effect Control**: If metadata indicates batches, permutation is stratified by batch ID (FR-007). **Fallback**: If batch metadata is missing, the pipeline runs **Surrogate Variable Analysis (SVA)** to detect and correct for latent batch effects before modeling.

### Handling of Constraints
* **p >> n (More features than samples)**: If metabolite count > sample count, PCA will be applied to the top variance metabolites before training (Edge Case handling).
* **Missing Data**: k-NN imputation (k=5) as per FR-002.
* **Multiple Testing**: BH correction ensures False Discovery Rate (FDR) < 0.10.

### Compute Feasibility (CPU-First)
* **Memory**: Data loaded in chunks or fully if < 500 rows. Random Forest `n_estimators=100` fits comfortably in 7 GB RAM.
* **Time**: A large number of permutations on a moderate sample size with 100 trees is estimated at ~30-60 minutes on a 2-core CPU., well within the 6-hour limit.
* **No GPU Required**: The plan explicitly avoids deep learning or large language models.

## Risk Assessment

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **No Real Metabolomic Data Available** | **Fatal**: Pipeline cannot run. | Use verified HuggingFace dataset. If fails, abort with clear error. |
| **Resistance Metric Missing/Non-numeric** | High | Graceful failure with specific error message (US-1 Edge Case). |
| **p >> n Overfitting** | Medium | Automatic PCA dimensionality reduction if features > samples. |
| **Permutation Test Timeout** | Medium | Limit iterations to [deferred] (as specified). Monitor runtime. |
| **Batch Effects** | Medium | Stratified permutation or SVA if metadata missing. |

## Decision Rationale

* **Why Random Forest?** It is the standard for tabular biological data, interpretable via feature importance, and requires no GPU.
* **Why Permutation Testing?** Standard ML validation (train/test split) is insufficient for small biological datasets where overfitting is likely. Permutation testing provides a rigorous null baseline.
* **Why BH Correction?** With hundreds of metabolites, uncorrected p-values guarantee false positives. BH controls the expected proportion of false discoveries.
* **Why CPU-Only?** The spec and constraints (GitHub Actions free tier) mandate it. The chosen methods are mathematically sound on CPU for this scale.