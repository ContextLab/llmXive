# Research: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Dataset Strategy

The study requires two datasets: American Gut Project (AGP) and UK Biobank (UKBB). Both must contain 16S rRNA amplicon data and self-reported dietary fiber intake.

### Verified Datasets & Access Strategy

| Dataset | Required Variables | Verified Source (URL) | Access Strategy | Feasibility Note |
|---------|-------------------|-----------------------|-----------------|------------------|
| **American Gut Project (AGP)** | 16S OTU table, Sample ID, Fiber (g/day), Age, BMI, Antibiotic use | **openmicrobiome/human_gut_microbiome** | Use `datasets.load_dataset()`  |  Fallback dataset if AGP/UKBB access fails. |
| **UK Biobank (UKBB)** | 16S OTU table, Sample ID, Fiber (g/day), Age, BMI, Antibiotic use | **openmicrobiome/human_gut_microbiome** | Use `datasets.load_dataset()` | Fallback dataset if AGP/UKBB access fails. |
| **Open Substitute** | 16S OTU table, Fiber (g/day), Covariates | HuggingFace datasets (e.g., `openmicrobiome/human_gut_microbiome`) | Use `datasets.load_dataset()` for verified open sources. | Only used if primary sources are inaccessible. |

**Decision**: The plan prioritizes the primary datasets (AGP/UKBB) but includes a robust fallback mechanism. If the programmatic fetch fails (due to access gates), the pipeline will use the `openmicrobiome/human_gut_microbiome` dataset.

### Data Preprocessing & Harmonization

1. **Unit Harmonization**: Convert all fiber intake values to `g/day`. If units are `mg/day`, divide by 1000.
2. **Filtering**:
   - Exclude samples with sequencing depth < 5,000 reads.
   - Exclude samples with fiber intake < 0 or > 200 g/day (implausible).
   - Exclude samples with missing fiber intake.
3. **Covariate Handling**:
   - Exclude samples with >20% missing covariates.
   - Impute remaining missing covariates (median for numeric, mode for categorical).
4. **PII Scan**: Scan all metadata for PII (names, emails, IDs) and exclude or redact.

## Statistical Methodology

### 1. Compositional Transformation
- **Method**: Centered Log-Ratio (CLR) transformation.
- **Pseudocount**: Add a small constant to all counts before log transformation to handle zeros (as per Edge Cases).
- **Rationale**: Microbiome data is compositional (unit-sum constraint). CLR transforms data to log-ratio space, making it suitable for standard statistical tests.
- **Scope**: Applied **ONLY** for MaAsLin2 and correlation analysis. **NOT** applied to ANCOM-II or DESeq2.

### 2. Association Analysis (MaAsLin2)
- **Model**: Linear model: `CLR_Taxon ~ Fiber + Age + BMI + Antibiotic_Use + Batch`.
- **Correction**: Benjamini-Hochberg FDR correction across all taxa.
- **Output**: Effect size (beta), p-value, q-value, standard error.
- **Rationale**: MaAsLin2 is designed for microbiome data, handles covariates, and supports FDR correction.

### 3. Differential Abundance (ANCOM-II & DESeq2)
- **Groups**: High-fiber vs. Low-fiber (defined by continuous fiber intake).
- **Methods**:
  - **ANCOM-II**: Primary method (compositional-aware). Operates on raw counts with internal log-ratio transformation.
  - **DESeq2**: Secondary method (robustness check). Operates on **raw counts** with internal median-of-ratios normalization. **NOT** on CLR-transformed data.
- **Output**: q-value, effect size, direction.
- **Rationale**: ANCOM-II is recommended for compositional data; DESeq2 provides a count-based alternative. Using DESeq2 on CLR data would violate its statistical assumptions.

### 4. Cross-Cohort Validation
- **Logic**: Compare significant taxa (q < 0.05) from AGP and UKBB.
- **Replication**: Flag taxa as "Replicated" if significant in both cohorts with consistent direction.
- **Non-Replicable**: Flag as "Non-Replicable" if significant in only one.
- **Rationale**: Validates findings across independent cohorts, increasing confidence in the results.

### 5. Power Analysis
- **Method**: Calculate power per cohort (AGP, UKBB) for the expected effect size (small to moderate) using Spearman's rank correlation coefficient (ρ).
- **Output**: Power value, margin of error.
- **Rationale**: Required to distinguish true null effects from underpowered results.

## Compute Feasibility

- **CPU-First**: All methods have CPU-tractable implementations.
- **Streaming**: Large datasets are streamed using `datasets.load_dataset(..., streaming=True)` to avoid memory overflow.
- **Runtime**: Estimated < 6 hours on CPU.

## Ethical & Reproducibility Considerations

- **Reproducibility**: All random seeds pinned. Data checksummed. Code versioned.
- **Data Hygiene**: No PII in committed data. Raw data preserved unchanged.
- **Transparency**: All assumptions (e.g., pseudocount = 1) documented. Limitations acknowledged.