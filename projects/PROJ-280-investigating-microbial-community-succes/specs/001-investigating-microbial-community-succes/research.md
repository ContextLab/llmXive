# Research: Investigating Microbial Community Succession in Constructed Wetlands

## Overview

This research phase defines the dataset strategy, statistical methods, and feasibility analysis for the microbial succession pipeline. It addresses the "how" of the implementation plan, ensuring alignment with the spec and constitution.

**Critical Data Note**: The pipeline relies on real public data. If no verified dataset containing both 16S feature tables and N/P removal metrics is found, the pipeline halts. No synthetic data is used.

## Dataset Strategy

### Verified Sources
The project relies on pre-processed 16S rRNA feature tables and metadata from public repositories. The following verified datasets (or their programmatic equivalents) are the **only** sources for data retrieval:

| Dataset Name | Verified URL / Loader | Relevance |
|--------------|-----------------------|-----------|
| *No Verified Wetland Dataset* | N/A | **Critical Gap**: The provided "Verified datasets" block contains no verified 16S wetland datasets with N/P removal metrics. |

### Data Gap Protocol
**Decision**: The implementation plan must **halt** if no verified 16S wetland dataset is found.

**Rationale**:
1.  **Constraint**: The prompt explicitly states: "For DATASETS specifically... cite ONLY the URLs listed in the # Verified datasets block... NEVER invent or guess a dataset URL."
2.  **Mismatch**: The listed URLs are for NLP, OCR, or generic text. None are 16S rRNA tables.
3.  **Action**: The `code/01_retrieve_data.py` script will:
    *   Attempt to load from the provided `data/config/dataset_ids.json`.
    *   Check against the verified sources list.
    *   If no match is found, log a **CRITICAL DATA GAP** error and exit with code 1.
    *   **No synthetic data is generated**. This ensures scientific validity and prevents tautological results.

**Fallback Research Question**:
If the data gap persists, the project will shift to a **Descriptive Community Profiling** study:
*   *Question*: "What is the composition of microbial communities in constructed wetlands reported in public literature?"
*   *Method*: Aggregate available 16S data (without N/P metrics) and report taxonomic abundance distributions.
*   *Limitation*: Cannot test succession or nutrient removal hypotheses.

### Dataset Variable Fit
*   **Required Variables**: 16S feature table (OTU/ASV counts), Metadata (Wetland Stage: early/intermediate/mature, N removal rate, P removal rate).
*   **Verified Data Fit**: **None of the verified URLs contain these variables.**
*   **Mitigation**: The pipeline will halt if real data is not found. The fallback descriptive analysis will use available 16S data without N/P metrics.

## Statistical Rigor

### Diversity & PERMANOVA (FR-004, FR-005, FR-009, FR-014)
*   **Method**: Alpha diversity (Shannon, Simpson) via `scikit-bio`. Beta diversity (Bray-Curtis) via `scikit-bio`.
*   **Hypothesis Testing**: PERMANOVA (Adonis) via `scikit-bio`.
*   **Post-hoc Testing**: Pairwise comparisons use **restricted permutations** to account for non-independence of distance matrix rows.
*   **Multiple Comparison**: Benjamini-Hochberg FDR correction applied to pairwise stage comparisons (FR-009).
*   **Power Analysis**: `statsmodels` will be used to estimate power based on observed effect size (R²) and sample size.
    *   **Gate**: If `power < 0.8` or `n < 10/group`, the pipeline **halts** and reports "UNDERPOWERED". No tentative results are generated.
*   **Effect Size**: R² values are reported alongside p-values. Small effects (R² < 0.1) are flagged as statistically significant but ecologically weak.

### Network Construction (FR-006, FR-007, FR-013)
*   **Method**: Spearman correlation matrix.
*   **Threshold**: |ρ| ≥ 0.6, p ≤ 0.01 (FDR corrected).
*   **Under-determined Check**: If `n_samples < n_taxa`, the network is flagged as 'under-determined' and **modularity calculation is skipped** to avoid spurious results (FR-013).
*   **Sensitivity**: A sweep of correlation thresholds (0.5 to 0.8) will be performed to assess stability of modularity changes (FR-013).
*   **Collinearity**: Variance Inflation Factor (VIF) calculated for taxa used in regression. VIF > 5 flagged (FR-010).

### Correlation & Regression (FR-008, FR-010)
*   **Method**: Spearman correlation.
*   **Validation**: **No formal cross-validation** will be performed due to sample size constraints (n=30, p>>n) which would lead to severe overfitting.
*   **Output**: List of taxa with |r| ≥ 0.5 and p ≤ 0.05. Results are treated as **exploratory/descriptive**.

## Feasibility & Compute Constraints

*   **Memory**: 7 GB RAM limit.
 * *Strategy*: Data is subsampled to max [deferred] reads per sample. Large count tables are processed in chunks if necessary.
*   **CPU**: 2 cores, 6 hours.
    *   *Strategy*: No GPU. All libraries (`scikit-bio`, `scipy`, `networkx`) are CPU-optimized. Network construction is O(N^2) but limited by the number of taxa (usually < 1000 after filtering).
*   **Disk**: 14 GB limit.
    *   *Strategy*: Intermediate files are cleaned up; only final processed tables and results are retained.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No verified 16S dataset available** | Pipeline cannot run on real data. | **Data Gap Protocol**: Pipeline halts immediately. Fallback to descriptive profiling if required. |
| **Sample size < 10 per stage** | PERMANOVA underpowered. | FR-014 ensures a hard stop; results are not generated. |
| **n < p (Samples < Taxa)** | Network construction invalid. | FR-013 flags as 'under-determined'; modularity comparison is skipped. |
| **Missing N/P metadata** | Cannot correlate taxa with function. | FR-002 filters out such samples; exclusion count logged. |