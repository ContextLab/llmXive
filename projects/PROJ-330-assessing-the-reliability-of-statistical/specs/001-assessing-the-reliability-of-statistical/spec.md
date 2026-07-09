# Specification: Assessing the Reliability of Statistical Significance in Openly Available Genomic Datasets

## Overview
This document defines the requirements for a pipeline that assesses the reliability of statistical significance (p-values) and effect sizes in genomic datasets from public repositories (GEO, TCGA, ENCODE).

## User Stories

### US1: Stability of Effect Size Calculation (P1)
As a researcher, I want to calculate the stability of effect sizes (log2 fold-changes) across stratified subsets of a dataset, so that I can determine if the reported effect sizes are robust to sampling variation.

### US2: Stratified Block Permutation Null Modeling (P2)
As a researcher, I want to generate a null distribution of p-values via stratified block permutations using a Fixed-Dispersion Wald Perturbation approximation, so that I can compare parametric p-values against empirical ones without exceeding 6-hour runtime constraints.

### US3: Cross-Dataset Benchmarking (P3)
As a researcher, I want to aggregate results across multiple datasets from different repositories (GEO, TCGA, ENCODE), so that I can determine if reliability metrics vary by data source.

## Functional Requirements

### FR-001: Data Loading
The system must fetch RNA-seq count matrices from GEO, TCGA, and ENCODE via a manifest file.

### FR-002: Preprocessing
The system must filter zero-count genes and handle missing batch metadata by defaulting to random stratification.

### FR-003: Effect Size Calculation
The system must calculate Pearson correlation of log2FC between the full dataset and stratified subsets for ALL genes to avoid Winner's Curse (see Spec Correction #1).

### FR-004: Null Model Generation
The system must generate a null distribution via stratified block permutations.
**SPEC CORRECTION #3 (Authorized by T021a):** To meet the 6-hour runtime constraint, FR-004 is explicitly authorized to use the **"Fixed-Dispersion Wald Perturbation"** approximation. This method skips the full Differential Expression (DE) re-run (DESeq2/edgeR) for every permutation. Instead, it:
1. Runs the full DE analysis ONCE to extract fixed dispersion parameters and model structure.
2. Shuffles sample labels within batch groups.
3. Recomputes Wald statistics using the fixed dispersions from step 1.
4. This approximation is required for CPU-only feasibility and is the approved implementation strategy for US2.

### FR-005: Metric Comparison
The system must compare parametric p-values against empirical p-values using a Kolmogorov-Smirnov (KS) test.

### FR-006: Visualization
The system must generate Bland-Altman plots and p-value histograms.

### FR-007: Multiple Testing Correction
The system must apply Benjamini-Hochberg correction to all reported p-values.

## Non-Functional Requirements

### NFR-001: Runtime Limit
The entire analysis for a single dataset must complete within 6 hours. The Fixed-Dispersion approximation (FR-004) is critical to meeting this constraint.

### NFR-002: Data Integrity
All downloaded datasets must be verified via checksums.

## Data Model
- **Dataset**: { source: str, id: str, count_matrix: pd.DataFrame, metadata: pd.DataFrame }
- **AnalysisResult**: { stability_correlation: float, pvalue_inflation: float, ks_statistic: float, ks_pvalue: float }

## Constraints
- **Winner's Curse Avoidance**: Effect size stability MUST be calculated on ALL genes, not just significant ones (Spec Correction #1).
- **Runtime**: Permutation tasks MUST use the Fixed-Dispersion approximation (Spec Correction #3).
- **KS Threshold**: A KS test p-value > 0.05 indicates uniform distribution (Spec Correction #2).