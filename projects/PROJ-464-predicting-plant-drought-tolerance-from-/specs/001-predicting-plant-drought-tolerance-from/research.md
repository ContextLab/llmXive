# Research: Predicting Plant Drought Tolerance from RSA Data

## Problem Statement

Can Root System Architecture (RSA) metrics (depth, branching density, surface area) extracted from images predict plant drought tolerance (measured as stomatal conductance and photosynthetic rate under water stress)?

**Critical Note on Classification**: The study will **NOT** create a 'drought tolerance class' by binarizing the target physiological variables (stomatal conductance/photosynthesis) themselves. This would create a circular validation loop (predicting X from Y where Y determines the class of X). Classification (Random Forest) and sensitivity analysis are performed **only** if an **independent tolerance proxy** (e.g., survival rate, biomass under stress) is available in the dataset. If no independent proxy is found, the study is framed strictly as "predicting physiological state" via regression, and classification steps are skipped entirely.

## Dataset Strategy

The pipeline relies on the following verified datasets. No other sources will be used.

| Dataset | Type | Verified Source URL | Usage |
|:--- |:--- |:--- |:--- |
| **NPPN (via MGB3)** | Image/Parquet | ` | Source of root images/traits. This verified source contains the NPPN data required by FR-001. |
| **TRY** | CSV | ` | Source of physiological traits (stomatal conductance, photosynthesis) and species metadata. |
| **Phylogenetic Tree** | Phylogeny | Open Tree of Life API (with strict halt on failure) | Source of phylogenetic tree for PGLS. **If API fails, pipeline halts.** PVR is not a fallback as it requires a tree. |

**Data Overlap & Feasibility**:
The success of this study depends on the intersection of species present in the RSA dataset (NPPN/MGB3) and the physiological dataset (TRY).
- **Requirement**: The NPPN/TRY overlap must contain at least **55 distinct species** to ensure sufficient statistical power (Cohen's f2=0.15, alpha=0.05, power=0.80, k=3 predictors).
- **Power Analysis**: T003 calculates required N based on effect size. If N < 55, the pipeline halts.
- **Missing Data**: If TRY lacks physiological data for a species in the RSA set, that species is excluded (listwise deletion) to avoid imputation bias.
- **Proxy Requirement**: If no independent tolerance proxy (survival/biomass) is found, classification is skipped.

## Methodological Rationale

### 1. RSA Extraction (US1)
- **Method**: CPU-optimized image processing using `opencv-python-headless` and `scikit-image`.
- **Metrics**: Root depth (max Y coordinate), Branching density (nodes/length), Surface area (pixel count * scale factor).
- **Constraint**: Must run on CPU cores, 7GB RAM. Large images will be downsampled if necessary.

### 2. Statistical Analysis (US2)
- **Correlation**: Spearman rank correlation to handle non-normal distributions common in biological data.
- **Regression**:
 - **PCA**: Applied to RSA traits to reduce dimensionality and handle collinearity.
 - **Interpretation**: PCA components are interpreted as "associational patterns of the RSA spectrum". Independent biological effects are **NOT** claimed for these components.
 - **Model**: Random Forest Regression (RF) for non-linear relationships, Linear Regression (OLS) for interpretability.
 - **Phylogenetic Correction**:
 - **Primary**: PGLS (using `statsmodels` or equivalent). Requires N >= 55.
 - **Fallback**: **NONE**. If the Open Tree of Life API fails to provide a tree, the pipeline halts. PVR is mathematically impossible without a distance matrix derived from a tree.
- **Multiple Comparison Correction**: Bonferroni or Benjamini-Hochberg (FDR) applied to all hypothesis tests (depth, branching, surface area).
- **Causal Framing**: Results are explicitly framed as "associational" due to the observational nature of the data.
- **Cross-Validation**: **Species-Level GroupKFold** (5-fold) is used to prevent phylogenetic leakage. The `groups` parameter is set to `species_name`.

### 3. Classification & Sensitivity (US3)
- **Proxy Requirement**: Classification is performed **only** if an independent tolerance proxy (e.g., survival rate) is found.
- **Thresholding**: If proxy exists, binarize *proxy* using median value (FR-007) to create "High" vs. "Low" drought tolerance classes.
- **Model**: Random Forest Classification.
- **Sensitivity Analysis**: The decision threshold is swept on the **predicted probability** output of the Random Forest (not the physiological metric) by ±0.05 (and other defined steps) to generate a curve of False Positive Rate (FPR) vs. False Negative Rate (FNR).
- **Reporting**: If no independent proxy is found, sensitivity analysis is marked "N/A" with a justification that classification was skipped to avoid circular validation.

### 4. Compute Feasibility
- **Hardware**: A minimal set of CPU cores and RAM.
- **Strategy**:
 - Data is loaded in chunks or sampled if >7GB.
 - No GPU usage.
 - `scikit-learn` models use default CPU settings.
 - Image processing is parallelized across CPU cores but memory-bounded.
- **Runtime**: Target <6 hours for 10k images. If exceeded, the pipeline logs a warning but continues with the processed subset.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **NPPN via MGB3** | NPPN data is available via the verified MGB3 HuggingFace dataset. This satisfies FR-001 without violating data integrity principles. |
| **PGLS with Strict Halt** | PGLS is standard for phylogenetic correction. PVR is rejected as a fallback because it requires a tree. If the tree is missing, no phylogenetic correction is possible, and the study cannot proceed (FR-010 violation). |
| **No Median-Split Classification** | Binarizing the target variable creates circular validation. Classification is only performed if an independent proxy exists. |
| **Spearman Correlation** | Biological data often violates normality assumptions; Spearman is more robust. |
| **No Causal Claims** | Observational data cannot support causal inference; framing as associational is required by FR-004. |
| **PCA as Associational Patterns** | PCA components are linear combinations of definitionally related variables. Interpreting them as independent causal drivers is invalid. They are reported as "associational patterns". |
| **N >= 55 for Power** | Power analysis (f2=0.15, alpha=0.05, power=0.80, k=3) yields N=55. N < 55 results in a halt. |
| **Probability Sweep** | Sensitivity analysis sweeps the predicted probability threshold, not the physiological metric, to avoid conflation with binarization. |
| **PVR Rejected** | PVR requires a distance matrix from a tree. Without a tree, PVR is impossible. The pipeline halts instead. |
| **GroupKFold** | Standard KFold allows species leakage. GroupKFold (groups=species) is required for phylogenetic independence. |