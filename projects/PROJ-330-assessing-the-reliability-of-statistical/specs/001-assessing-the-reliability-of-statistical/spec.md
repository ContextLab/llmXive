# Specification: Assessing the Reliability of Statistical Significance in Openly Available Genomic Datasets

## 1. Introduction

### 1.1 Purpose
This document specifies the requirements for a pipeline that assesses the reliability of statistical significance (p-values) in genomic differential expression analysis using publicly available datasets. The pipeline evaluates stability of effect sizes and validity of parametric assumptions via stratified permutation testing.

### 1.2 Scope
The system will:
- Download and preprocess RNA-seq count matrices from GEO, TCGA, and ENCODE.
- Calculate effect size stability via subset correlation.
- Generate null distributions using stratified block permutations with a Fixed-Dispersion Wald Perturbation approximation.
- Compare parametric vs. empirical p-values and report inflation metrics.

## 2. User Stories

### US1: Stability of Effect Size Calculation
As a researcher, I want to calculate the stability of log2 fold-changes across stratified subsets of a dataset so that I can assess the robustness of the effect size estimates.

### US2: Stratified Block Permutation Null Modeling
As a statistician, I want to generate a null distribution via stratified block permutations using the Fixed-Dispersion Wald Perturbation strategy so that I can validate the parametric p-value assumptions without incurring the full computational cost of re-running DE models.

### US3: Cross-Dataset Benchmarking
As a bioinformatician, I want to aggregate results across multiple repositories (GEO, TCGA, ENCODE) to determine if statistical reliability varies by data source.

## 3. Functional Requirements

### FR-001: Data Ingestion
The system shall fetch datasets from verified sources (GEO, TCGA, ENCODE) via a manifest file and verify checksums.

### FR-002: Preprocessing
The system shall filter zero-count genes and handle missing batch metadata by defaulting to random stratification.

### FR-003: Effect Size Stability
The system shall calculate the Pearson correlation of log2 fold-changes between the full dataset analysis and stratified subset analyses.

### FR-004: Fixed-Dispersion Wald Perturbation (Spec Correction #3)
**UPDATE**: To meet the 6-hour runtime constraint, the system is explicitly authorized to use the "Fixed-Dispersion Wald Perturbation" approximation.
- The system shall extract dispersion parameters from the initial full-dataset DE analysis (DESeq2/edgeR).
- The system shall skip full re-estimation of dispersions during permutation iterations.
- The system shall recompute Wald statistics using the fixed dispersions and permuted labels.
- This approximation is validated by plan.md Spec Correction #3, which confirms that dispersion estimates are stable across permutations and that re-estimation is computationally prohibitive for the required iteration counts (N >= 1000).

### FR-005: Null Distribution Generation
The system shall generate a null distribution of Wald statistics by shuffling sample labels within batch groups (stratified) and applying the Fixed-Dispersion approximation.

### FR-006: Effect Size Scope (Spec Correction #1)
**UPDATE**: The system shall calculate stability on "ALL genes", not just significant genes.
- This change overrides previous interpretations that focused only on significant genes.
- Calculating on all genes prevents "Winner's Curse" bias where effect sizes are inflated in significant subsets.
- This is authorized by plan.md Spec Correction #1.

### FR-007: P-Value Comparison
The system shall compare parametric p-values (from the full model) against empirical p-values (from the permutation null distribution).

### FR-008: Multiple Testing Correction
The system shall apply Benjamini-Hochberg correction to all reported p-values.

### FR-009: Visualization
The system shall generate Bland-Altman plots comparing parametric vs. empirical log-p-values.

### FR-010: Aggregation
The system shall aggregate metrics across datasets, grouped by source repository.

## 4. Non-Functional Requirements

### NFR-001: Runtime
The full permutation analysis must complete within 6 hours for standard datasets (N=20-50 samples). The Fixed-Dispersion approximation (FR-004) is mandatory to satisfy this constraint.

### NFR-002: Memory
The system must operate within 6GB RAM.

### NFR-003: Reproducibility
All random seeds must be configurable and logged.

## 5. Data Model

### 5.1 Manifest File
JSON file defining dataset sources, URLs, and checksums.

### 5.2 State File
YAML file tracking artifact hashes, dataset versions, and analysis parameters.

### 5.3 Results Artifact
CSV/JSON containing stability metrics, p-value comparisons, and inflation statistics.

## 6. Appendix

### Spec Correction Log
- **Correction #1**: FR-006 updated to use "ALL genes" for stability calculation.
- **Correction #2**: KS test threshold clarified (p-value > 0.05 implies uniformity).
- **Correction #3**: FR-004 updated to authorize "Fixed-Dispersion Wald Perturbation" to meet runtime constraints.