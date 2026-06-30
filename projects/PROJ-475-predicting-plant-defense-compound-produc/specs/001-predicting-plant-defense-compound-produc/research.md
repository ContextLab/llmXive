# Research: Predicting Plant Defense Compound Production from Public Genomic and Environmental Data

## Research Summary

This project investigates the association between genomic diversity, environmental context, and defense compound production in *Arabidopsis thaliana*. The core hypothesis is that higher genomic diversity (heterozygosity) correlates with increased defense compound abundance, mediated by environmental stressors.

**Important Note on Current Execution**: Due to the absence of verified public URLs for the specific *Arabidopsis* 1001 Genomes VCFs and PhenolExplorer compound data required by the spec, this project currently operates in **Mock Data Mode**. The pipeline is validated for architectural correctness, statistical logic, and reproducibility, but **no empirical biological conclusions** regarding the Heterozygote Advantage hypothesis can be drawn from the current run.

## Dataset Strategy

The analysis requires three distinct data modalities: Genomic Variants, Environmental Metadata, and Defense Compound Profiles.

**Constraint**: The spec assumes data availability from NCBI SRA (VCF), WorldClim/GBIF, and PhenolExplorer/ChemBank. However, the **Verified datasets** block provided for this project contains NO verified sources for VCF files, NCBI SRA raw data, or specific Plant Defense Compound databases. The available verified datasets are generic text/image/CSV dumps (e.g., NCBI Disease, GBIF occurrence records, Wikipedia chunks) that **do not contain the required variables** (SNPs, specific plant population coordinates, defense compound concentrations).

**Decision**:
1. **Dataset Mismatch**: The verified dataset block does not contain the specific *Arabidopsis* 1001 Genomes VCFs or PhenolExplorer compound data required by FR-001, FR-002, and FR-003.
2. **Mock Data Strategy**: To proceed with the *methodological* implementation and testing of the pipeline (FR-005 through FR-008) without violating the "No invented URLs" rule, the pipeline will generate a **Mock Dataset** that mimics the expected schema and statistical properties of the target data. This dataset is generated deterministically from a seed to ensure reproducibility.
3. **Real Data Fallback**: If a verified URL for the specific *Arabidopsis* data becomes available in the future, the ingestion script can be pointed to it. For now, the `ingestion.py` module will default to the mock generator to ensure the pipeline is runnable and testable.

| Data Type | Required Variables | Verified Source (URL) | Status |
|:--- |:--- |:--- |:--- |
| **Genomic (VCF)** | SNPs, Population ID, Coordinates | **NO VERIFIED SOURCE** (Spec FR-001) | **Mock Generation** |
| **Environmental** | Temp, Precip, Soil pH, Coordinates | **NO VERIFIED SOURCE** (Spec FR-002) | **Mock Generation** |
| **Compounds** | Compound ID, Concentration, Population ID | **NO VERIFIED SOURCE** (Spec FR-003) | **Mock Generation** |
| **GBIF (Reference)** | Species occurrence (coords) | ` | **Available but not specific to target species/compound data** |

*Note: The GBIF parquet files listed are for general species occurrences (e.g., beetles, generic flora) and do not contain the specific genomic or compound data required. They cannot be used as a direct substitute for the 1001 Genomes or PhenolExplorer data.*

## Methodology & Statistical Rigor

### 1. Data Preprocessing
- **Imputation**: SNPs with >20% missingness are imputed via mean allele frequency (per edge case).
- **Population Structure Control**: Principal Component Analysis (PCA) will be performed on the genomic data (or a subset of high-variance SNPs). The top N PCs will be included as covariates in the regression model to control for ancestry confounding (addressing concern: methodology-6fb622d8).
- **Aggregation**: All data aggregated to `population_id`.
- **Normalization**: Defense compounds Z-scored per source study (FR-011).

### 2. Model Training
- **Algorithm**: ElasticNet (LASSO/Ridge hybrid) via `sklearn.linear_model.ElasticNet`.
- **Cross-Validation**:
 - If $N \ge 30$: 5-fold CV.
 - If $N < 30$: Leave-One-Out CV (LOOCV).
- **Covariate Logic**: If $N < 30$ AND `unique_studies >= N-1`, the 'source_study' covariate is excluded to prevent model singularity, and global Z-score normalization is used (FR-010).
- **Collinearity**: Variance Inflation Factor (VIF) calculated. Predictors with VIF > 5 flagged but retained (per Assumption about collinearity).

### 3. Statistical Validation
- **Permutation Test**: 1,000 shuffles of the outcome variable. Null distribution of R² generated. P-value = (count(R²_null >= R²_obs) + 1) / (n + 1).
- **Sensitivity Analysis**: Alpha swept over {0.01, 0.05, 0.1}. Jaccard index calculated for top 10 features across sweeps.
- **Multiple Comparisons**: Benjamini-Hochberg procedure applied to p-values of coefficients.

### 4. Scientific Validity & Limitations
- **Mock Data Limitation**: The current run uses mock data. Any significant p-values or R² values found are **artifacts of the data generation process** and do not validate the biological hypothesis (Heterozygote Advantage). The pipeline is being tested for *structural* correctness (can it run? does it calculate statistics correctly?), not *empirical* validity.
- **Causal Inference**: Data is observational. Claims are strictly associational.
- **Power**: If $N < 30$, power is limited; LOOCV used to maximize data usage, but confidence intervals will be wide.
- **Untestable Hypothesis**: The core scientific inquiry (GxE interaction on defense compounds) remains untestable until verified real-world datasets are available.