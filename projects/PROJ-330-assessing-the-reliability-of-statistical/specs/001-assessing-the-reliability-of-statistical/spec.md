# Feature Specification: Assessing the Reliability of Statistical Significance
# Version: 1.2 (Updated by T024c)

## Overview
This feature implements an automated pipeline to assess the reliability of statistical
significance in openly available genomic datasets (GEO, TCGA, ENCODE). The core goal
is to determine if parametric p-values are well-calibrated against a stratified block
permutation null model.

## User Stories

### US1: Stability of Effect Size Calculation (P1 - MVP)
- **Goal**: Calculate the stability of log2 fold-changes across stratified subsets.
- **Metric**: Pearson correlation of log2FC between full dataset and subsets.
- **Scope**: ALL genes (to avoid Winner's Curse).

### US2: Stratified Block Permutation Null Modeling (P2)
- **Goal**: Generate a null distribution via stratified block permutations using the
 Fixed-Dispersion Wald Perturbation strategy.
- **Validation**: Compare parametric p-values against the empirical null distribution.
- **Correction**: The statistical validity check uses the Kolmogorov-Smirnov (KS) test.
 **CRITICAL**: The null hypothesis (uniform distribution) is accepted if the KS test
 **p-value > 0.05** (not D < 0.05). A low D-statistic with a low p-value (due to
 massive sample size) indicates rejection of uniformity, which is the desired failure
 mode for unreliable p-values.

### US3: Cross-Dataset Benchmarking (P3)
- **Goal**: Aggregate results across GEO, TCGA, and ENCODE to identify repository-specific
 reliability trends.

## Functional Requirements

### FR-001: Data Ingestion
- System must fetch RNA-seq count matrices from GEO, TCGA, and ENCODE via a manifest.
- Checksums must be verified (SHA256).

### FR-002: Preprocessing
- Filter zero-count genes.
- Handle missing batch metadata by defaulting to random stratification.

### FR-003: Differential Expression
- Run DESeq2/edgeR via R script wrapper.
- Extract fixed-dispersion parameters for the permutation step.

### FR-004: Permutation Null Model
- Implement Fixed-Dispersion Wald Perturbation (skip full DE re-run).
- Shuffle sample labels within batch groups.
- Cap runtime at 6 hours; fallback to min 100 iterations.

### FR-005: Metric Calculation
- **Stability**: Pearson correlation of log2FC (ALL genes).
- **Calibration**: KS test comparing empirical vs. parametric p-values.
 - **Condition**: Pass if KS p-value > 0.05.
- **Inflation**: Median Absolute Deviation (MAD) of p-values.

### FR-006: Reporting
- Generate Bland-Altman plots.
- Apply Benjamini-Hochberg correction to reported p-values.
- Aggregate metrics by data source (US3).

## Spec Corrections Log

- **SC-001 (T016a)**: Effect size stability must be calculated on "ALL genes", not just
 significant ones, to avoid Winner's Curse bias.
- **SC-002 (T024c)**: The KS test threshold for uniformity must be interpreted as
 **p-value > 0.05** (accept null) rather than D < 0.05. The D-statistic alone is
 insufficient due to sample size sensitivity; the p-value determines the statistical
 conclusion.
- **SC-003 (T021a)**: Fixed-Dispersion Wald Perturbation is authorized to meet 6h runtime.