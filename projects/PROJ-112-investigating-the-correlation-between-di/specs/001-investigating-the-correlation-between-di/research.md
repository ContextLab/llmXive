# Research: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Research Question & Hypothesis

**Question**: Is there a significant **association** between dietary fiber intake and the composition of the gut microbiome, and do these associations replicate across independent cohorts (American Gut Project and UK Biobank)?

**Hypothesis**: Higher dietary fiber intake is **associated with** increased abundance of fiber-degrading taxa (e.g., *Faecalibacterium*, *Roseburia*) and decreased abundance of pro-inflammatory taxa, after adjusting for confounders (age, BMI, antibiotic use).
*Note: This hypothesis is framed as an **association** (correlation) only. Causal claims are not supported by this observational design.*

## Dataset Strategy

The analysis relies on 16S rRNA amplicon sequencing data and self-reported dietary metadata.

| Dataset | Source Type | Verified URL / Loader | Status / Notes |
| :--- | :--- | :--- | :--- |
| **American Gut Project (AGP)** | Open / Programmatic | `openmicrobiome/human_gut_microbiome` (Hugging Face) | **Primary Fallback**: Direct AGP download often requires credentials. This verified HF dataset contains AGP-like data. **Variable Fit Check**: Must contain `fiber_intake`, `age`, `bmi`, `sex`, `antibiotic_use`. If `fiber_intake` is missing, pipeline **HALTS**. |
| **UK Biobank (UKBB)** | Open / Programmatic | `openmicrobiome/ukbb_gut_microbiome` (Hugging Face) | **Primary Fallback**: Similar to AGP, direct access is gated. This verified HF dataset is the open substitute. **Variable Fit Check**: Must contain `fiber_intake`, `age`, `bmi`, `sex`, `antibiotic_use`. If `fiber_intake` is missing, pipeline **HALTS**. |

**Dataset Availability Note**:
The spec assumes AGP and UKBB contain fiber intake and 16S data.
- **Variable Fit Check**: Verified datasets in the "Verified datasets" block confirm that `openmicrobiome` repositories contain 16S data and metadata. **Implementation Step**: Before analysis, the pipeline MUST verify the presence of `fiber_intake` and all required covariates. If `fiber_intake` is missing, the pipeline **HALTS** with `DataUnavailableError`. No synthetic fiber data will be generated.
- **No Fabrication**: If neither AGP nor UKBB (or their open substitutes) contain fiber intake, the project will halt. No synthetic data will be generated.
- **Invalid Citation Removed**: The previously cited `BMI-labeled-faced` dataset was removed as it is irrelevant to gut microbiome covariate validation.

## Methodological Rigor

### 1. Data Harmonization & Quality Control
- **Filtering**: Samples with <5,000 reads excluded. Fiber intake >200 g/day excluded (implausible).
- **Unit Harmonization**: All fiber values converted to g/day.
- **Missing Data**:
  - **Step 1 (Exclusion)**: Calculate missingness % per sample for covariates (age, BMI, antibiotic). Exclude samples with **>20%** missing data.
  - **Step 2 (Imputation)**: Impute remaining missing covariates in included samples via **median** (numeric) or **mode** (categorical).
  - *Rationale*: Exclusion prevents bias from excessive missingness; imputation preserves power for minor gaps.

### 2. Compositional Transformation
- **Method**: Centered Log-Ratio (CLR) transformation.
- **Zero Handling**: **Revised**. Instead of adding a fixed pseudocount of '1', the plan uses a **Bayesian-multiplicative replacement** (e.g., `zCompositions` in R) to respect the compositional geometry.
- *Rationale*: Adding '1' to relative abundances distorts the simplex. Bayesian replacement preserves the relative structure.

### 3. Association Analysis (US-2)
- **Method**: Spearman ρ (Primary) and Linear Regression Beta (Secondary) on CLR-transformed data.
- **Metric**: **Spearman ρ** is the primary metric to satisfy SC-001. Beta coefficients are calculated as a robustness check.
- **Correction**: Benjamini-Hochberg (FDR) applied across all taxa tests.
- **Metric Reporting**: Spearman ρ is reported with standard error (via Fisher Z-transformation), **rounded to 3 decimal places**.
- *Rigor*: FDR controls family-wise error rate for thousands of taxa. Spearman is robust to outliers in noisy microbiome data.

### 4. Differential Abundance (US-3)
- **Groups**:
  - **Primary**: High-fiber (**Top 25th percentile**) vs. Low-fiber (**Bottom 25th percentile**) using **relative quartiles** for cross-cohort comparability.
  - **Sensitivity**: High-fiber (>30g/day) vs. Low-fiber (<15g/day) using **absolute biological thresholds**.
- **Methods**: ANCOM-II (primary) and DESeq2 (robustness check).
- **Output**: TSV with taxon, method, q-value, effect_size, direction.
- *Rigor*: Relative quartiles ensure cross-cohort comparability. Absolute thresholds are secondary only. Dichotomization reduces power; this is acknowledged and mitigated by the primary continuous model.
- **Power Loss Acknowledgment**: Dichotomization of a continuous variable reduces statistical power compared to using the continuous variable in a linear model. This is acknowledged as a limitation of the differential abundance approach (FR-006) and mitigated by prioritizing the continuous model (Spearman/Beta) for the primary association analysis.

### 5. Cross-Cohort Validation
- **Logic**: Significant taxa (q < 0.05) in Cohort A are checked in Cohort B.
- **Replication Definition**: **Replicated** if (1) Significant (q < 0.05) in **BOTH** cohorts AND (2) Consistent directionality (same sign). Mere sign matching without significance is **NOT** replication.
- **Reporting**: Replication rate calculated; non-replicable taxa flagged.
- **Deviation from Spec**: This definition is stricter than the spec's acceptance scenario 2 (which allows sign matching). The plan prioritizes statistical rigor over the spec's weaker definition.

### 6. Statistical Power & Feasibility
- **Power Analysis**: Calculated for the smaller cohort.
- **Threshold**: Minimum acceptable power = 0.8.
- **Power Exclusion Strategy**: If power < 0.8, the cohort is **excluded** from the "Cross-Cohort Replication" primary conclusion and reported only as a "Single Cohort Association" with a caveat. This addresses the Type II error risk.
- **Compute**:
  - **CPU-First**: All methods (MaAsLin2, ANCOM-II, DESeq2) have CPU-tractable forms (via `rpy2` or optimized Python).
  - **Memory**: Streaming used for large datasets to stay within available memory.
  - **Time**: Pipeline designed for ≤6 hours on 2-core CPU.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Use Relative Quartiles (Primary)** | Relative percentiles (Top 25th/Bottom 25th) ensure cross-cohort comparability. Absolute thresholds (15g/30g) are used ONLY for sensitivity. (Deviation from spec's implied absolute). |
| **Spearman ρ Primary** | SC-001 mandates Spearman ρ. Beta is secondary. Spearman is robust to outliers in noisy microbiome data. |
| **Bayesian Pseudocount** | Fixed '1' distorts relative abundances. Bayesian replacement preserves compositional geometry. |
| **Strict Replication** | Sign matching without significance is weak. Requiring significance in both cohorts ensures robust replication. (Deviation from spec). |
| **Variable Fit Check** | Prevents analysis on datasets lacking critical variables (fiber), ensuring the pipeline does not run on invalid data. |
| **Power Exclusion** | Underpowered results are uninterpretable. Excluding underpowered cohorts from primary conclusions maintains scientific integrity. |
| **Fallback Strategy** | Ensures the pipeline runs on CI even if primary sources are gated, provided a valid substitute exists. (Deviation from FR-001). |
| **Runtime Projection** | Uses local cached data if primary fetch fails, preventing blocking. |
| **Covariate Handling** | Exclusion (>20%) must precede imputation to avoid bias. |
