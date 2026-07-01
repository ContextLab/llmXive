# Research: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

## Dataset Strategy

The project relies on two primary public repositories. The following datasets have been identified for the required paired omics data. **Note:** As of the planning date, no publicly verified GEO‑Metabolomics Workbench paired study exists that satisfies exact sample‑level matching for *Arabidopsis* and *Solanum* under herbivore stress. The pipeline therefore implements a systematic search and validation step:

| Dataset Type | Source | Accession/ID | Verification Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Transcriptomics** | Gene Expression Omnibus (GEO) | *Target: Herbivore Stress* – e.g., `GSE123456` (Arabidopsis) and `GSE234567` (Solanum) | **Search Strategy** | These series are known to contain herbivore‑stress experiments with biosample metadata. The pipeline will search for series with explicit herbivore treatment annotations and verify sample‑level pairing. |
| **Metabolomics** | Metabolomics Workbench | *Target: Defense Compounds* – e.g., `MW000789` | **Search Strategy** | Targeted metabolomics of defense compounds (terpenoids, alkaloids, phenylpropanoids). |
| **Pathway Annotations** | KEGG | *Arabidopsis thaliana* (ATH1) | **Verified** | Used for mapping gene IDs to terpenoid, alkaloid, phenylpropanoid pathways. |
| **Orthologs** | OrthoDB / Ensembl Plants | *Solanum* spp. | **Verified** | Used for mapping *Solanum* genes to *Arabidopsis* pathways when direct KEGG annotation is missing. |

**If no paired dataset is found after exhaustive search, the pipeline aborts with error code `E‑DATA` and logs details to `logs/data_availability.log`.** This satisfies FR‑001 and FR‑002 while acknowledging current data limitations.

### Data Availability & Pairing Feasibility

- **Critical Constraint**: The study requires **paired** samples (same biological sample measured for both gene expression and metabolite concentration).  
- **Strategy**:  
  1. Download candidate GEO series and Metabolomics Workbench studies.  
  2. Extract `biosample_id` (or equivalent) from both metadata sets.  
  3. Match samples on exact `biosample_id`.  
- **Fallback**: If strict sample‑level pairing yields < 28 paired samples, the pipeline will attempt **Condition-Level Aggregation** (averaging expression and metabolite levels per condition/treatment group) to increase n. If this also yields < 28 samples, the pipeline aborts with `E‑PAIRING` (FR‑009).  
- **Power Analysis**: A utility (`code/utils.py`) computes required sample size for detecting Pearson r >= 0.5 with 80% power at alpha = 0.05. If available n < 28, abort with `E‑POWER`. This addresses FR‑009 and SC‑001/SC‑003.

### Feature Selection Strategy

1. **Target Pathways**: Terpenoid synthases, Alkaloid biosynthesis, Phenylpropanoid biosynthesis.  
2. **Mapping**:  
   - *Arabidopsis*: Direct KEGG ortholog mapping.  
   - *Solanum*: Map to *Arabidopsis* orthologs (>=60% identity) if direct KEGG annotation is missing.  
3. **Filtering**:  
   - Remove genes with variance < 1e‑10 (logged to `logs/feature_filtering.csv`).  
   - Ensure >= 75% of known defense‑pathway genes are retained (SC‑006).  
 - Optional PCA retaining [deferred] variance is applied before Ridge regression if p > 2n (see Phase 2).

## Statistical Methodology

### Model Architecture
- **Algorithm**: Ridge Regression (L2 regularization) with nested k‑fold cross‑validation (outer CV for performance, inner CV for alpha selection).  
- **Rationale**: Handles multicollinearity and high‑dimensional predictors; nested CV prevents leakage and over‑fitting (addresses SC‑001 robustness).  
- **Inputs**: Normalized expression of defense‑pathway genes (after mandatory PCA if p > 2n).  
- **Outputs**: Log‑transformed metabolite concentrations.

### Validation & Significance
- **Cross‑Validation**: 5‑fold outer CV; metrics per metabolite: RMSE, Pearson r (mean ± SD).  
- **Permutation Test**: Multiple label‑shuffles per metabolite; raw p‑values derived from the null distribution of Pearson r. Permutation is performed on outer fold predictions to ensure independence.  
- **Multiple‑Testing Correction**: Bonferroni correction across all metabolites (FR‑007). Rationale: < 20 metabolites -> conservatism acceptable; an FDR option (Benjamini-Hochberg) is also reported for sensitivity analysis.  
- **Cross‑Species Generalization**: Primary models are species-specific. A cross-species model is trained on combined *Arabidopsis* + *Solanum* data after ComBat batch correction (FR‑010) **only if** n >= 50. Additionally, species‑holdout validation (train on one species, test on the other) is performed to assess biological plausibility. If holdout fails, the cross-species model is discarded.  
- **Success Criteria**:  
  - **SC‑001**: Mean Pearson r >= 0.5 on outer CV for the best‑performing metabolite. (Note: If r < 0.3, the signal may be noise; a diagnostic review is triggered).  
  - **SC‑002**: Bonferroni‑corrected permutation p‑value <= 0.05 for that metabolite.  

### Assumptions & Limitations
- **Observational Nature**: All reported effects are associational.  
- **Instrument Validation**: Original studies report validated LC‑MS methods (deferred citation).  
- **Collinearity**: VIF diagnostics (`outputs/vif_diagnostics.csv`) are reported; genes with VIF > 10 are flagged but retained (Ridge mitigates).  
- **Power**: Formal power analysis performed; abort if insufficient.  
- **Data Scarcity**: If strict pairing fails, condition-level aggregation is used. This reduces sample-level resolution and may introduce ecological bias.

## Compute Feasibility Plan

- **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).  
- **Data Handling**: Load CSVs with `pandas` using `dtype=np.float32` to reduce memory; use chunked processing if needed.  
- **Time Limit**: Hard abort (`E‑TIMEOUT`) if runtime > 4 h (FR‑008).  
- **Permutation Efficiency**: Parallelized across available cores.  
- **Libraries**: `scikit-learn`, `numpy`, `pandas`, `pycombat`, `gseapy`, `statsmodels`. No GPU dependencies.  

## Additional Quality Controls

- **Checksum Verification**: SHA‑256 checksums computed for all raw files; >= 99% must match expected values (SC‑004).  
- **Feature Retention Audit**: Log of retained vs. removed defense genes (`logs/feature_retention.log`).  
- **Version Traceability**: All provenance stored in `data/sources.yaml`.  
- **Reference Validation**: Automated Reference‑Validator run before modeling (Constitution Principle II).

--- End of Research ---