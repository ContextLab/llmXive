# Feature Specification: Assessing the Reliability of Statistical Significance in Openly Available Genomic Datasets

## Overview
This feature implements a pipeline to assess the reliability of statistical significance findings in openly available genomic datasets (GEO, TCGA, ENCODE). The pipeline evaluates the stability of effect sizes and the validity of p-value distributions under stratified block permutations.

## User Stories

### US1: Stability of Effect Size Calculation
As a researcher, I want to calculate the stability of effect sizes (log2 fold-changes) across stratified subsets of a dataset, so that I can determine if my findings are robust to sampling variation.

**Acceptance Criteria:**
1. The system downloads a genomic dataset from a verified source (GEO, TCGA, ENCODE).
2. The system partitions the data into stratified subsets (or random stratification if batch metadata is missing).
3. The system calculates Differential Expression (DE) for the full dataset and each subset.
4. The system computes the Pearson correlation of log2FC values between the full dataset and each subset.
5. **CRITICAL**: Effect size stability is calculated on **ALL genes**, not just significant genes, to avoid Winner's Curse (see Spec Correction #1).

### US2: Stratified Block Permutation Null Modeling
As a researcher, I want to generate a null distribution via stratified block permutations, so that I can compare empirical p-values against parametric assumptions.

**Acceptance Criteria:**
1. The system performs stratified block permutations on sample labels.
2. The system uses the Fixed-Dispersion Wald Perturbation approximation to efficiently recompute Wald statistics.
3. The system generates a uniform p-value histogram and performs a KS test (p-value > 0.05 indicates uniformity).
4. The system produces a Bland-Altman plot comparing parametric vs. empirical p-values.

### US3: Cross-Dataset Benchmarking
As a researcher, I want to aggregate results from multiple distinct datasets, so that I can determine if reliability varies by repository.

**Acceptance Criteria:**
1. The system processes datasets from GEO, TCGA, and ENCODE.
2. The system aggregates stability correlations and inflation metrics, grouped by source.
3. The system generates comparative visualizations of reliability across repositories.

## Functional Requirements

### FR-001: Data Loading
The system must fetch datasets from GEO, TCGA, and ENCODE via a manifest file mechanism, verifying checksums.

### FR-002: Preprocessing
The system must filter zero-count genes and handle missing batch metadata by defaulting to random stratification.

### FR-003: Differential Expression
The system must perform DE analysis using DESeq2/edgeR (via R scripts) on full and subset datasets.

### FR-004: Null Modeling
The system must implement stratified block permutations using the Fixed-Dispersion Wald Perturbation strategy.

### FR-005: Metric Calculation
The system must calculate Pearson correlation of log2FC and KS statistics for p-value uniformity.

### FR-006: Stability Analysis Scope
**SPEC CORRECTION #1**: The system must calculate stability metrics on **ALL genes** present in the dataset, overriding any previous requirement to filter for "significant genes". This is to prevent Winner's Curse bias in effect size estimation.
*Reference*: plan.md Spec Correction #1.

### FR-007: P-Value Correction
The system must apply Benjamini-Hochberg correction to all reported p-values.

### FR-008: Visualization
The system must generate Bland-Altman plots and comparative bar charts.

## Non-Functional Requirements

### NFR-001: Runtime
The full pipeline must complete within 6 hours per dataset.

### NFR-002: Memory
Memory usage must remain below 6GB.

### NFR-003: Reproducibility
All random seeds must be configurable and logged.

## Spec Corrections Log

1. **Spec Correction #1 (FR-006)**: Changed stability calculation scope from "significant genes" to "ALL genes" to avoid Winner's Curse. Cited in plan.md.
2. **Spec Correction #2 (FR-005)**: Clarified KS test threshold: p-value > 0.05 (not D < 0.05) indicates uniformity.
3. **Spec Correction #3 (FR-004)**: Authorized Fixed-Dispersion Wald Perturbation approximation to meet runtime constraints.

## Data Model

### Dataset
- `source`: str (GEO, TCGA, ENCODE)
- `accession_id`: str
- `count_matrix`: pd.DataFrame (genes x samples)
- `metadata`: pd.DataFrame (sample info)
- `batch_column`: str (optional)

### AnalysisResult
- `dataset_id`: str
- `stability_correlation`: float (Pearson r)
- `p_value_inflation`: float (MAD)
- `ks_statistic`: float
- `ks_p_value`: float
- `source`: str

## Artifacts

- `data/raw/`: Downloaded raw datasets
- `data/processed/`: Preprocessed count matrices
- `artifacts/figures/`: Generated plots (Bland-Altman, bar charts)
- `artifacts/results/`: JSON/CSV summary tables
- `state.yaml`: Artifact hashes and run metadata