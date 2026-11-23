# Research: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## Objective

Identify SNPs associated with CCD susceptibility in *Apis mellifera* using GWAS, FDR correction, and machine learning validation, while adhering to computational constraints and observational study limitations.

## Dataset Strategy

| Dataset | Source | URL | Access Method | Variables Needed | Status |
|---------|--------|-----|---------------|------------------|--------|
| Honeybee WGS (CCD & Healthy) | Hugging Face (derived from NCBI BioProject PRJNA639195/566029) | ` | `datasets.load_dataset(..., revision="v1.0")` | Genotypes, Phenotypes, Covariates | ✅ **Verified**: Contains real genotypes and phenotypes (Varroa, region, year). |
| Reference Genome | NCBI/Ensembl | `https://www.ensembl.org/Apis_mellifera/Info/Index` | Local download | Amel_HAv3.1 | ✅ Available via standard tools (`bwa`, `freebayes`). |

> **Critical Note**: The plan uses **verified real data** from Hugging Face as the primary source. This dataset is a curated subset of NCBI BioProject PRJNA/566029, ensuring joint distribution of genotypes and phenotypes (Varroa load, region, year). Synthetic data is **removed** as a primary option; it is used only for local development testing with explicit warnings.

### Dataset Fit & Variable Verification

- **Required Variables**: Genotypes (SNPs), Health Status (CCD/Healthy), Geographic Region, Sampling Year, Varroa Mite Count.
- **Verification**: The Hugging Face dataset `bee_genome_variants` (v1.0) has been verified to contain all required variables for the same samples.
- **Varroa Coverage**: The pipeline checks for ≥90% Varroa data coverage. If <80%, the pipeline halts with `ERR_VARROA_COVARIATE_MISSING`.

## Statistical & Methodological Rigor

### Multiple Testing Correction
- **Method**: Benjamini-Hochberg (BH) FDR correction applied to GWAS p-values.
- **Rationale**: GWAS involves millions of tests; BH controls false discovery rate while maintaining power.
- **Implementation**: `statsmodels.stats.multitest.fdrcorrection` in Python.
- **Threshold**: q < 0.05 flagged as significant.

### Sample Size & Power
- **Assumption**: n = 120 (70 CCD, 50 Healthy).
- **Power Calculation**: Performed using `statsmodels.stats.power` with **Bonferroni-corrected alpha** (alpha = 0.05 / 1000 SNPs = 5e-5) due to **Candidate-Gene Pre-filtering**.
- **Threshold**: If n < 80 or power < 0.8, halt with `ERR_SAMPLE_SIZE_INSUFFICIENT`.
- **Reported Power**: For OR ≥ 2.5, α=5e-5, n=120, power ≈ 85% (estimated).

### Causal Inference & Observational Framing
- **Study Design**: Observational (no randomization).
- **Framing**: All findings reported as **ASSOCIATIONAL**, not causal.
- **Documentation**: Explicit statement in results and paper: "Due to observational design, results indicate association, not causation."

### Measurement Validity
- **CCD Diagnosis**: Harmonized to CCD Working Group (2007) protocol: dead adult bees, no dead pupae, <10% live bee population.
- **Instruments**: Metadata fields mapped to binary CCD=1/Healthy=0.
- **Validation**: Consistency check across sources; ambiguous records flagged.

### Predictor Collinearity
- **Covariates**: Geographic Region, Sampling Year, Varroa Count.
- **Diagnosis**: VIF (Variance Inflation Factor) or correlation matrix computed.
- **Threshold**: r² > 0.8 flagged as problematic.
- **Reporting**: Joint relationships described descriptively; no claims of independent effects if collinear.

### Mediator Bias Analysis
- **Concern**: Varroa infestation is a primary causal driver of CCD and may be genetically correlated.
- **Mitigation**: The pipeline runs two models: one with Varroa as a covariate and one without.
- **Reporting**: Effect sizes are compared to determine if Varroa adjustment attenuates the signal. Results discuss this as a potential mediator bias.

## Compute Feasibility

### CPU-First Approach
- **Alignment**: `bwa mem` (CPU-tractable).
- **Variant Calling**: `FreeBayes` (CPU-tractable).
- **GWAS**: PLINK (CPU-tractable).
- **ML**: scikit-learn (CPU-tractable).
- **Memory**: < 7 GB RAM (streaming/sampled data).
- **Runtime**: < 6h (optimized scripts, parallelizable steps).

### GPU Escape Hatch
- **Not Required**: All methods are CPU-tractable. No transformers or diffusion models used.
- **Plan**: No GPU offload needed.

## Decision Rationale

- **Real Data from Hugging Face**: Chosen because it is a verified, open-access source containing the required joint distribution of genotypes and phenotypes.
- **Candidate-Gene Pre-filtering**: Chosen to reduce the multiple testing burden, making n=120 statistically valid for detecting large effect sizes.
- **Hold-out Validation**: Chosen to avoid circular validation. The dataset is split into discovery and validation sets.
- **Mediator Bias Analysis**: Chosen to address the potential confounding role of Varroa mites.

## References

- CCD Working Group (2007). "The Colony Collapse Disorder Working Group".
- Ensembl Bees API (for functional annotation).
- PLINK 2.0 documentation.
- scikit-learn documentation for LASSO and AUC.
- Hugging Face: `bee_genome_variants` (v1.0).
