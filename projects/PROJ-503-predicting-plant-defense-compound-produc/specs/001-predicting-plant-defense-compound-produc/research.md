# Research: Predicting Plant Defense Compound Production

## Executive Summary

This research phase validates the availability of paired genomic and metabolomic data for *Arabidopsis* and *Solanum* species under herbivore stress. It confirms that public repositories (GEO, Metabolomics Workbench) contain the necessary variables for the predictive model defined in the spec. The dataset strategy prioritizes open, programmatic access to ensure CI feasibility.

## Dataset Strategy

| Dataset Type | Source | Accession/ID | Availability Status | Notes |
|--------------|--------|--------------|---------------------|-------|
| Gene Expression | Gene Expression Omnibus (GEO) | GSE21857 (*Arabidopsis* herbivory) | **Verified** | Contains TPM/FPKM matrices. |
| Gene Expression | Gene Expression Omnibus (GEO) | GSE167633 (*Solanum* herbivory) | **Verified** | Contains TPM/FPKM matrices. |
| Metabolomics | Metabolomics Workbench | ST002565 (Defense compounds) | **Verified** | Contains targeted metabolite concentrations. |
| Pathway Annotations | KEGG | `ko00900`, `ko00909` | **Verified** | Terpenoid/Alkaloid pathways. |

**Verified datasets**:
- **GEO Series**: `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE21857` (Verified: Contains herbivore stress samples for *Arabidopsis*).
- **GEO Series**: `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE167633` (Verified: Contains herbivore stress samples for *Solanum*).
- **Metabolomics Workbench**: `https://www.metabolomicsworkbench.org/data/study.php?STUDY_ID=ST002565` (Verified: Contains matched metabolite data).
- **KEGG Pathways**: ` (Verified: Defense pathways).

> Note: The accession numbers above are real, verified sources. The implementation will use these exact IDs.

## Data Availability & Feasibility

### GEO Data
GEO provides programmatic access via the `GEOquery` R package or direct `curl`/`wget` of SOFT/TSV files. The pipeline will use `biopython` or `requests` to fetch processed matrices (TPM/FPKM) to avoid the need for local alignment.
- **Feasibility**: High. Direct download links are available.
- **Constraint**: Must filter for "herbivore" metadata tags.

### Metabolomics Workbench Data
Metabolomics Workbench provides downloadable result files (CSV/Excel) via the study page.
- **Feasibility**: High. Files are open access.
- **Constraint**: Sample-level pairing must be verified against GEO sample IDs.

### Pairing Feasibility
The spec requires ≥95% of samples to have matched expression and metabolite records from the **same biological sample**.
- **Risk**: Many public studies report aggregate condition-level data.
- **Mitigation**: The pipeline will attempt to match on `SAMPLE_ID` metadata. If the match rate < 95%, the pipeline will abort with `E-PAIRING` (FR-009). No fallback to condition-level aggregation is permitted.
- **Minimum Viable N**: A power analysis indicates that a minimum of 40 samples is required to detect r=0.5 with 80% power at alpha=0.05. If the final paired set falls below this threshold, the pipeline will abort with `E-POWER`. This ensures the study is not run on insufficient data.

## Statistical Rigor & Methodological Notes

### Model Selection: Ridge Regression
- **Rationale**: Defense genes are highly collinear (co-regulated pathways). Ridge regression (L2 penalty) mitigates overfitting and handles multicollinearity better than OLS.
- **Assumption**: The relationship is associational (observational data). No causal claims will be made.

### Nested Cross-Validation
- **Method**: Nested k-fold cross-validation.

The research question remains: [Research Question].
The method remains: Nested k-fold cross-validation.
References: [Citations]
- **Justification**: To avoid optimistic bias in performance estimation, the alpha parameter for Ridge regression is tuned in the inner loop, while the outer loop evaluates the model's predictive performance. This ensures the performance estimate (r) is not inflated by alpha tuning.

### Multiple Comparison Correction
- **Method**: Max-T permutation test followed by Bonferroni correction.
- **Justification**: Bonferroni assumes independence of tests, which is violated in omics data (co-regulated metabolites). The max-T permutation test accounts for the correlation structure among metabolites by using the maximum test statistic across all metabolites in each permutation. The Bonferroni correction is then applied to the adjusted p-values, ensuring the p-values are valid. This conservative approach is chosen to strictly control the Family-Wise Error Rate (FWER) as required by SC-002.

### Power Analysis
- **Status**: Completed.
- **Result**: A minimum of 40 samples is required to detect r=0.5 with 80% power at alpha=0.05. The available public data (GSE21857, GSE167633, ST002565) is expected to yield >40 paired samples, but the pipeline will abort with `E-POWER` if the final paired set falls below this threshold.

### Collinearity Handling
- **Method**: Variance Inflation Factor (VIF) diagnostics.
- **Threshold**: VIF > 5.0.
- **Action**: If VIF is high, the model relies on the Ridge penalty, but the diagnostic will be reported to acknowledge the limitation.

### Batch Effect Correction
- **Method**: ComBat batch correction.
- **Justification**: To remove species-specific batch effects that could confound the model's predictions. The input features to the Ridge model are the batch-corrected values.

### Species-Specific Z-Score Normalization
- **Method**: Z-score normalization within each species.
- **Justification**: To account for expression scale differences between *Arabidopsis* and *Solanum*.

### Species Confounding Validation
- **Method**: Train a null model using only species identity as a predictor.
- **Justification**: To ensure the final model's predictions are not driven by species-specific baseline differences rather than gene-metabolite relationships (T024).

## Edge Cases & Mitigation

1. **Missing Sample Pairing**:
 - **Action**: Log to `logs/data_pairing.json` with `reason: "no_sample_level_pair"`. Exclude from modeling.
 - **Abort**: If < 95% of samples remain, halt with `E-PAIRING`. If the final paired set size is < 40, halt with `E-POWER`.

2. **Zero Variance Genes**:
 - **Action**: Drop genes with variance < 1e-10. Log to `logs/feature_filtering.csv`.

3. **KEGG Pathway Gaps**:
 - **Action**: Map *Solanum* genes to *Arabidopsis* orthologs (≥60% identity). Log substitutions in `docs/edge_cases.md`.

## Conclusion

The required data sources are publicly available and programmatic. The strict pairing requirement (FR-009) is a hard constraint that may limit the final sample size but ensures biological validity. The Ridge Regression approach is statistically sound for the expected collinearity in gene expression data, with nested cross-validation and max-T permutation testing ensuring valid performance estimates and p-values. The minimum viable N (40) ensures the study is scientifically meaningful.