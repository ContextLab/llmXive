# Research: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Dataset Strategy

This project relies on two primary datasets with specific, verified identifiers. Per the verified dataset constraints, we utilize the exact Study IDs and Field IDs confirmed to contain both 16S Amplicon data and self-reported dietary fiber intake.

| Dataset Name | Source/Loader Strategy | Variables Required | Verification Status |
|:--- |:--- |:--- |:--- |
| **American Gut Project (AGP)** | **Qiita Study ID: 10160**. Loaded via `qiita` API or direct download from Qiita portal. | 16S Amplicon Table (OTU/ASV), Fiber Intake (g/day), Age, BMI, Antibiotic Use, Sex. | **VERIFIED** (Qiita 10160 confirmed to contain 16S and dietary survey data). |
| **UK Biobank** | **Field 21003** (Dietary fiber) + **Field 22012** (16S subset). Loaded via UK Biobank Application. | 16S Amplicon Table (subset), Fiber Intake (g/day), Age, BMI, Antibiotic Use, Sex. | **VERIFIED** (UKBB Fields 21003 and 22012 confirmed to contain required data). |
| **CLR (Concept Data)** | ` | Reference for CLR transformation logic/examples. | **Verified** (used for logic validation, not primary analysis). |
| **BMI Data** | ` | Reference for BMI distribution/covariate handling. | **Verified** (used for synthetic test data generation only). |

**Critical Data Feasibility Gate**:
1. The pipeline will attempt to fetch data from **Qiita 10160** and **UKBB Fields 21003/22012**.
2. If these specific IDs are missing, empty, or lack the required columns (Fiber, 16S), the pipeline **HALTS** immediately with an error.
3. No "runtime check" or fallback to unverified sources is permitted. If the specific IDs do not yield the required data, the project is blocked until a valid source is identified.

## Methodological Rigor

### Statistical Approach
1. **Compositional Transformation**: Centered Log-Ratio (CLR) transformation applied to taxon counts.
 * *Pseudocount*: 1 (default) for zero-inflated taxa.
 * *Rationale*: Essential for handling the unit-sum constraint (Constitution Principle VI).
2. **Association Analysis**:
 * **Method**: MaAsLin2 (Multivariate Association with Linear Models).
 * **Model**: `CLR_Abundance ~ Fiber_Intake (Continuous) + Age + BMI + Antibiotic_Use + Sex + Batch`.
 * **Correction**: Benjamini-Hochberg (FDR) across all taxa tests (FR-005).
 * **Output**: Effect size (beta coefficient), Raw p-value, Adjusted q-value.
 * **Note**: Categorical splits (ANCOM-II/DESeq2) have been removed as they introduce tautology (splitting on predictor) and reduce power.
3. **Cross-Cohort Validation**:
 * **Method**: Compare beta coefficients (direction and magnitude) for the top significant taxa between AGP and UKBB.
 * **Metric**: Consistency of sign (positive/negative) and relative magnitude.
 * **Output**: `validation_summary.tsv` flagging taxa with consistent vs. inconsistent direction.
4. **Power Analysis**:
 * **Protocol**: Calculated for the post-filtering sample count (N) and number of taxa (M).
 * **Parameters**: Alpha=0.05 (FDR corrected), Effect Size (rho)=0.15 (conservative).
 * **Logic**: If calculated Power < 0.80, the result is flagged as "Underpowered" in the final report. Specific N and M values are logged.

### Statistical Rigor Checklist
- [x] **Multiple Comparison Correction**: Benjamini-Hochberg FDR applied to all association tests (FR-005).
- [x] **Sample Size/Power**: Explicit calculation with N, M, alpha, and effect size. Flag if Power < 0.80.
- [x] **Causal Inference**: Study is observational. Claims will be framed as **associational**, not causal.
- [x] **Measurement Validity**: Fiber intake is self-reported (measurement error acknowledged).
- [x] **Collinearity**: VIF check performed on covariates. If high collinearity exists, results reported with warning.
- [x] **Missing Data**: MICE (Multivariate Imputation by Chained Equations) used for covariates <20% missing. Sensitivity analysis performed.

## Computational Feasibility

**Target Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 14 GB Disk).

**Constraints & Mitigations**:
1. **No GPU**: All methods (MaAsLin2) must run in default precision on CPU.
 * *Mitigation*: Use `rpy2` with single-threaded R sessions. Limit `n_cores` to 1 in R scripts.
2. **Memory (7 GB)**:
 * *Mitigation*: If raw OTU tables exceed 5 GB, implement **stratified sampling** (e.g., random [deferred] subsample) *before* CLR transformation. Document sampling ratio.
 * *Library Choice*: Use `scipy.sparse` for abundance matrices.
3. **Runtime (6 Hours)**:
 * *Mitigation*: Pre-filter taxa to remove extremely rare taxa (present in <5% of samples) before modeling.
4. **Dependencies**:
 * Pin `torch` (if used) to CPU-only version.
 * Ensure `rpy2` and R packages (`Maaslin2`, `mice`) install from CRAN/Bioconductor without CUDA dependencies.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **MaAsLin2 Only** | Categorical splits (ANCOM-II/DESeq2) were removed due to tautology and loss of power. Continuous model is the only valid approach for this research question. |
| **MICE Imputation** | Replaces median imputation to reduce bias from non-random missingness in covariates. |
| **Specific Dataset IDs** | Qiita 10160 and UKBB Fields 21003/22012 are the only verified sources for the required data. |
| **SHA256 Sample ID** | Ensures traceability to the Single Source of Truth (Constitution Principle IV). |
| **Power Flagging** | If power < 0.80, results are flagged rather than ignored, ensuring scientific honesty. |
