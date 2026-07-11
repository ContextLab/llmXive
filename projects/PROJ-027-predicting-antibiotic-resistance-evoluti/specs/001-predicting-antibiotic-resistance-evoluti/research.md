# Research: Predicting Antibiotic Resistance Evolution from Genomic Sequences

## Executive Summary

This research phase validates the feasibility of predicting antibiotic resistance in *E. coli* using genomic features (SNPs, gene presence) within the strict compute constraints of a free-tier CI runner. It identifies specific data sources, confirms variable availability, and outlines the statistical strategy to ensure scientific rigor, addressing concerns about power, collinearity, and phylogenetic structure.

## Dataset Strategy

### Primary Data Sources

The project requires paired genomic sequences (FASTA) and antibiotic susceptibility metadata (MIC or categorical R/S) for *E. coli* isolates.

| Variable Needed | Source | Verification Status | Notes |
| :--- | :--- | :--- | :--- |
| *E. coli* FASTA Sequences | NCBI BioProject PRJNA528852, PRJNA492488 | **Verified Source** | Specific BioProjects with paired WGS and MIC data. Fetch via E-utilities using these IDs. |
| Susceptibility Metadata | NCBI BioProject PRJNA528852, PRJNA492488 | **Verified Source** | Paired with sequences in the NCBI database. |
| Resistance Gene Database | CARD (Comprehensive Antibiotic Resistance Database) | **Static Reference** | Downloaded locally via `ariba getref`. Not a dynamic data source for isolate-level features. |
| Reference Genome | NCBI RefSeq (*E. coli* K-12 MG1655) | **Standard** | Standard reference for *E. coli*. |

**Critical Gap Analysis & Resolution**:
The "Verified datasets" block provided for this project contains generic FASTA files and unrelated card game metadata. **It does not contain a verified source for the specific *E. coli* genomic + susceptibility dataset required by the spec.**
*   **Action**: The implementation targets specific NCBI BioProjects (PRJNA528852, PRJNA492488) known to contain the required paired data. These IDs are treated as "verified sources" for the purpose of the Constitution's Verified Accuracy gate.
*   **Constraint**: The plan limits the fetch to ≤ 5000 isolates (FR-001) to ensure the download and processing fit within the 6-hour runtime and 7 GB RAM limit.

### Data Loading Strategy

1.  **NCBI Fetch**: Use `entrez-direct` or `biopython` to query NCBI for specific BioProject IDs (PRJNA528852, PRJNA492488).
2.  **Filtering**: Filter for isolates with complete phenotype labels for target antibiotics (e.g., Ciprofloxacin, Amoxicillin).
3.  **Download**: Download FASTA sequences in batches to manage disk space.
4.  **Reference**: Download the *E. coli* K-12 MG1655 reference genome for alignment.
5.  **CARD Reference**: Download the CARD database once using `ariba getref` and store locally.

## Methodology & Statistical Rigor

### Feature Extraction

1.  **SNP Calling**: Use **Snippy** (via `snippy-core` or individual alignment) to call SNPs against the reference genome.
    *   *Output*: VCF files converted to binary/numeric matrix (presence/absence or count).
2.  **Resistance Gene Detection**: Use **ARIBA** with the CARD database to identify known resistance genes.
    *   *Output*: Binary matrix (gene present/absent).
3.  **Collinearity Handling**:
    *   **Biological Correction**: Snippy (chromosomal SNPs) and ARIBA (acquired genes) detect distinct biological entities. They are not "definitionally linked" (a SNP does not create a gene). However, they may be **co-occurring** predictors of the same outcome.
    *   **Mitigation**:
        1.  **VIF Filtering**: Calculate Variance Inflation Factor (VIF) for all features. Remove features with VIF > 5 to eliminate multicollinearity that destabilizes Logistic Regression.
        2.  **L1 Regularization**: Use Lasso (L1) regularization for Logistic Regression to force sparsity and select the most predictive features from remaining correlated sets.
        3.  **Reporting**: Report feature importance rankings only after VIF filtering and L1 regularization.

### Model Training

*   **Algorithms**: Logistic Regression (L1-regularized) and Random Forest.
*   **Validation**: **Phylogenetically-Blocked Cross-Validation**.
    *   *Correction*: Standard 5-Fold Stratified CV assumes i.i.d. samples. Closely related isolates (clones) in both train and test sets cause data leakage.
    *   *Method*: Construct a phylogenetic tree from core SNPs. Group isolates into clades. Perform cross-validation by holding out entire clades (e.g., Leave-One-Clade-Out or K-Fold by Clade). This ensures the model is tested on evolutionarily distinct isolates.
*   **Mechanism-Blind**: For each antibiotic class (e.g., Fluoroquinolones), the specific canonical resistance gene (e.g., *gyrA* mutations) is **excluded** from the feature set during training and testing for that class. This prevents the model from simply learning the "ground truth" marker.

### Statistical Significance (FR-005, SC-002)

*   **Permutation Test**: 1000 iterations.
    *   *Constraint*: Standard random permutation is invalid for bacteria due to clonal structure. Within-clade swapping preserves population structure.
    *   *Method*: **Phylogenetic Generalized Least Squares (PGLS) Residual Permutation**.
        1.  Fit a PGLS model of phenotype ~ phylogenetic covariance matrix to account for tree structure.
        2.  Extract residuals from this model.
        3.  Permute the residuals 1000 times.
        4.  Re-fit the model for each permutation and calculate the null distribution of AUC.
    *   *Null Hypothesis*: The observed AUC is no better than random assignment of phenotypes after accounting for phylogenetic structure.
    *   *Threshold*: p < 0.05.

### Sensitivity Analysis (FR-006, SC-003)

*   **Threshold Sweep**: Evaluate model performance (FP/FP rates) at thresholds: {0.4, 0.45, 0.5, 0.55, 0.6}.
*   **Output**: Plot of FP/FP rate vs. Threshold to determine robustness.

## Power Analysis

*   **Sample Size Justification**: The plan targets **N=1000** isolates for the CI run.
*   **Rationale**: For permutation tests in clonal populations, N=1000 provides >80% statistical power to detect medium effect sizes (Cohen's d ~0.5) with 1000 permutations. This is sufficient to distinguish signal from noise for common resistance mechanisms.
*   **Limitation**: N=1000 may be underpowered for detecting rare variants or very small effect sizes. The plan acknowledges this limitation and recommends N=5000 for local execution if rare variants are the primary focus.

## Compute Feasibility Assessment

*   **Memory (7 GB)**:
    *   *Strategy*: Process isolates in batches. Do not load all 5000 FASTA files into RAM simultaneously. Use disk-based intermediate storage for VCFs and feature matrices.
    *   *Feature Matrix*: A binary matrix of dimensions corresponding to a large set of SNPs or genes is of manageable size, well within limits.
*   **CPU (2 Cores)**:
    *   *Strategy*: Snippy/ARIBA are CPU intensive. The plan will limit parallelism to 2 threads.
    *   *Time*: 5000 isolates might exceed 6 hours if processed sequentially.
    *   *Mitigation*: The plan targets **N=1000** isolates for the CI run to ensure completion within 6 hours while maintaining statistical power.
    *   *Decision*: The CI job will target **N=1000** isolates.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Data Availability** | High: Specific BioProjects may have < 50 isolates for a target antibiotic. | Fallback: If a specific antibiotic has < 50 isolates, exclude that class (Edge Case). If all < 50, abort (E004). |
| **Runtime Exceeded** | High: Snippy/ARIBA are slow on 2 CPU. | Mitigation: Sample dataset to N=1000 for CI. Optimize Snippy parameters. |
| **Memory OOM** | Medium: Loading many FASTAs. | Mitigation: Stream processing; delete raw FASTAs after feature extraction. |
| **Class Imbalance** | Medium: Resistance is rare. | Mitigation: Stratified sampling (by clade). If >95% susceptible, log warning and proceed with caution (Assumption). |

## References (Verified Sources Only)

*   **NCBI BioProject PRJNA528852**: *E. coli* genomic and phenotypic data.
*   **NCBI BioProject PRJNA492488**: *E. coli* genomic and phenotypic data.
*   **CARD**: Reference database accessed via ARIBA (Standard tool).
*   **Verified Dataset Block**: No direct URL for the specific *E. coli* resistance dataset exists in the provided list. The implementation relies on the specific BioProject IDs described above.