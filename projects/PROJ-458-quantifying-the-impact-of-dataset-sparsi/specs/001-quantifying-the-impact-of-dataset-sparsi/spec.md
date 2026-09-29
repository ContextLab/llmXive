# Specification: Quantifying the Impact of Dataset Sparsity on Model Performance
## Version 1.1 (Aligned with Plan Deviations)

## 1. Introduction
This document defines the requirements for a research pipeline to quantify the impact of dataset sparsity on the predictive performance of machine learning models for materials science. The study utilizes the Materials Project (MP) database and employs Linear Mixed-Effects Modeling (LMM) to account for nested data structures.

## 2. Functional Requirements

### FR-001: Data Acquisition
The system shall download a corpus of at least 150,000 material entries from the Materials Project API using the provided `MP_API_KEY`.

### FR-002: Data Filtering
The system shall filter the raw pool to retain only entries where `formation_energy` is not null and `dft_computed` is True.

### FR-003: Representative Stratified Sample (RSS)
The system shall construct a Representative Stratified Sample (RSS) of 30,000 entries from the filtered pool. The sampling must preserve the distribution of formation energy. The RSS serves as the 100% baseline for all sparsity experiments.

### FR-004: Descriptor Generation
The system shall generate elemental property descriptors using `matminer` (atomic_number, electronegativity, atomic_radius).

### FR-005: Sparsity Levels
The system shall generate strictly nested stratified subsets corresponding to the following sparsity levels: **1, 2, 5, 10, 25, 50, 100**. These levels represent the percentage of the RSS used for training.

### FR-006: Linear Mixed-Effects Modeling (LMM)
The system shall employ Linear Mixed-Effects Modeling (LMM) to analyze the relationship between sparsity and error. The fixed effect is `sparsity_level`, and the random effect is `seed` (nested structure). The model formula is `error ~ sparsity_level + (1|seed)`.

### FR-007: Sensitivity and Slope Variance Threshold
The system shall perform a sensitivity analysis to measure the variance in the slope of the learning curve between consecutive sparsity levels. The analysis must explicitly report whether the **slope variance < 10%** between consecutive levels. This threshold is used to determine if adding more data yields diminishing returns. The system shall output `data/results/slope_variance.json`.

### FR-008: Reporting
The system shall generate a final report summarizing findings as associational evidence, avoiding causal claims.

## 3. Success Criteria

### SC-001: Metric Logging
All metrics (RMSE, MAE, Variance, Calibration Slope) must be logged to `data/results/metrics.csv`.

### SC-002: Learning Curve Visualization
The system shall generate a learning curve plot (Error vs. Dataset Size) with error bars representing standard deviation across seeds.

### SC-003: Statistical Significance via LMM
The system shall apply pairwise contrasts with Tukey-adjusted p-values to the LMM results to report p-values for differences between sparsity levels (threshold p < 0.05). The analysis must confirm that the **slope variance < 10%** threshold is met or violated for specific intervals, providing statistical backing for the sensitivity analysis defined in FR-007.

## 4. User Stories

### US-1: Data Ingestion Pipeline
As a researcher, I want to ingest and preprocess the Materials Project data so that I have a clean, feature-rich dataset for training.

### US-2: Sparsity Subsampling and Training
As a researcher, I want to generate nested subsets and train models on CPU so that I can measure performance degradation as a function of data size.

### US-3: Statistical Analysis and Validation
As a researcher, I want to perform Linear Mixed-Effects Modeling (LMM) and validate the **slope variance < 10%** threshold so that I can rigorously quantify the impact of dataset sparsity and determine diminishing returns.

## 5. Assumptions & Constraints
- **MP_API_KEY**: The `MP_API_KEY` environment variable must be set. The system will raise a `RuntimeError` if missing.
- **CPU Only**: All training and inference must run on CPU.
- **Memory Limit**: The system must enforce a memory limit of ~7GB RAM.
- **No Synthetic Data**: All data must come from the real Materials Project API. Synthetic fallbacks are strictly forbidden.
- **Reproducibility**: All random seeds must be fixed and logged.

## 6. Data Lineage
- Raw: `data/raw/raw_pool.csv`
- Filtered: `data/processed/filtered_pool.csv`
- Descriptors: `data/processed/descriptors_pool.csv`
- Final Pool: `data/processed/full_pool_final.csv`
- RSS: `data/processed/rss_pool.csv`
- Sparsity Subsets: `data/processed/sparsity_<level>pct.csv`
- Test Set: `data/processed/test_set.csv`
- Metrics: `data/results/metrics.csv`
- Slope Variance: `data/results/slope_variance.json`