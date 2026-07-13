# Research: Investigating the Relationship Between Gut Microbiome Composition and Mental Health in Public Datasets

## Dataset Strategy

The primary analysis requires a **single verified public dataset** that contains both 16S rRNA sequencing data and valid mental health questionnaire responses (PHQ-9, GAD-7) for the same individuals.

| Dataset | Source URL | Role in Analysis | Notes |
|---------|------------|------------------|-------|
| **AGP Microbiome + PHQ-9** | *NO verified source found* | Primary Analysis | **Critical Gap**: No single verified public dataset was found containing both AGP 16S data and linked PHQ-9/GAD-7 scores for the same samples. |
| **AGP Microbiome (Standalone)** | ` | Reference Only | Contains 16S rRNA data but **NO** linked mental health metadata. Cannot be used for primary analysis. |
| **PHQ-9 Synthetic** | ` | Unit Testing Only | **NOT** used for analysis. Used only to validate pipeline logic in `tests/unit/`. |
| **BMI Data** | *NO verified source found* | Covariate | No general population health dataset with linked microbiome and BMI was found. If BMI is not in the primary dataset, analysis proceeds without it. |
| **GAD-7 Scores** | *NO verified source found* | Secondary Outcome | **Gap Identified**: No verified source for GAD-7. |

**Decision: Data Availability Gate**
- **Observation**: The spec assumes AGP (Study ID 10317) contains both microbiome and mental health data. Verified sources show AGP is microbiome-only, and mental health data is either synthetic or unlinked.
- **Action**: The pipeline will **not** attempt to merge unlinked datasets (e.g., AGP microbiome + Synthetic PHQ-9). Merging unlinked data creates a biologically invalid dataset that cannot answer the research question.
- **Protocol**: If no single verified dataset with linked data is found, the pipeline **halts at Phase 0** and outputs a "Data Gap Report". No statistical analysis (correlation, PERMANOVA) will be performed on unlinked or synthetic data.

## Methodological Rationale

### 1. Preprocessing (FR-002)
- **Rarefaction vs. VST**: The spec mandates rarefaction to equal sequencing depth. If >20% sample loss occurs, VST is required.
- **Decision**: We will use `scipy.stats` for rarefaction logic. If the rarefaction depth threshold results in >20% sample exclusion, the code will automatically switch to `DESeq2`-style VST (approximated via `skbio` or `sklearn`'s `PowerTransformer`).
- **Filtering**: Taxa with <0.1% prevalence will be removed to reduce noise and computational load.

### 2. Statistical Analysis (FR-004, FR-005)
- **Correlation**: Instead of simple partial Spearman correlation (which lacks power for high-dimensional data), we will use **MaAsLin2-style linear modeling** (or `skbio.stats.composition` with linear models). This method includes built-in regularization and covariate adjustment suitable for microbiome data.
 - *Rationale*: MaAsLin2 is designed for high-dimensional microbiome data and handles covariates (age, BMI) robustly.
- **Multiple Testing**: Benjamini-Hochberg (BH) correction will be applied to all p-values derived from taxon-level tests to control the False Discovery Rate (FDR).
- **PERMANOVA**: `skbio.stats.ordination.permanova` will be used to test for differences in beta diversity between high/low depression groups.
 - *Covariate Handling*: We will use **distance matrix residualization** (regressing out age/BMI from the distance matrix) followed by the PERMANOVA test, and/or use the `strata` argument to restrict permutations by covariates.

### 3. Computational Feasibility (CPU-Only)
- **Constraints**: 2 CPU cores, 7GB RAM, 6h runtime.
- **Strategy**:
 - Data will be loaded as Pandas DataFrames. If the dataset is >4GB, we will sample rows (e.g., `df.sample(n=1000)`) to fit memory, noting this in the report.
 - No GPU-accelerated libraries (e.g., `torch`, `tensorflow`) will be used.
 - `maaslin2` (CPU wheel) or `skbio` is preferred for diversity metrics and modeling as they are optimized for CPU.

## Decision Log

| Decision | Rationale | Impact |
|----------|-----------|--------|
| **Abort on Data Mismatch** | Merging unlinked datasets (AGP + Synthetic PHQ-9) creates biologically invalid data. | If no linked dataset is found, the pipeline halts. No "simulation" results are generated. |
| **PHQ-9 only (GAD-7 dropped)** | No verified source for GAD-7 found. | Scope reduced to PHQ-9. GAD-7 analysis skipped with log warning. |
| **MaAsLin2 over Partial Spearman** | Partial Spearman is underpowered for high-dimensional data. | Increased statistical rigor for covariate adjustment and multiple testing. |
| **Distance Residualization for PERMANOVA** | Strata alone is insufficient for covariate adjustment in PERMANOVA. | Ensures confounders (age, BMI) are properly controlled. |
| **Unit Test Only for Synthetic Data** | Synthetic data lacks biological validity. | Synthetic PHQ-9 used ONLY for `tests/unit/` to validate code logic, not for scientific results. |

## Risk Assessment

1. **Data Gap**: High risk that no single verified dataset contains both AGP 16S and PHQ-9.
 * *Mitigation*: Pipeline halts at Phase 0 with a clear "Data Gap" report. No invalid results are generated.
2. **Memory Overflow**: High risk if full OTU table is loaded.
 * *Mitigation*: Implement chunked loading or sampling logic in `data_ingestion.py`.
3. **Statistical Power**: Low sample size after filtering may yield non-significant results.
 * *Mitigation*: Report effect sizes and confidence intervals. Perform KS test on p-values (SC-002) to check for uniformity.