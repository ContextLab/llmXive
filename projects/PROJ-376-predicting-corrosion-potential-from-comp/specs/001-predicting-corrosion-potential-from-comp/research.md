# Research: Predicting Corrosion Potential from Composition and Environment

## 1. Dataset Strategy

The project relies on the **NIST Corrosion Database (NIST-IR-8200)** as the primary source for the joint distribution of alloy composition, environmental conditions, and corrosion potential.

### Verified Sources
Per the project constraints, only the following sources are verified. Note that **NIST-IR-8200** currently has **NO verified source** in the provided block.

| Dataset Name | Verified URL | Status |
|:--- |:--- |:--- |
| **NIST-IR-8200** | *No verified source found* | **CRITICAL GAP**: The spec assumes this dataset exists and contains the required variables. The provided "Verified datasets" block does not contain a URL for NIST-IR-8200 corrosion data. |
| **NIST 800-53** | ` | **Verified** (Note: This URL points to NIST 800-53, a cybersecurity framework, NOT corrosion data. This is a mismatch and cannot be used.) |

**Critical Mismatch Analysis**:
The provided "Verified datasets" block does not contain a verified URL for the NIST Corrosion Database (NIST-IR-8200).
- **Impact**: The plan cannot proceed with data ingestion from a verified source if the dataset does not exist in the verified list.
- **Action**: The implementation MUST attempt to fetch from the official NIST public repository (if accessible via standard HTTP) or halt with a `DataInsufficientError` if no valid, reachable source is found. The spec explicitly states: "If the intersection is < 500 samples, the project MUST halt."
- **Decision**: The `download_nist.py` script will attempt to locate the official NIST IR-8200 data. If no verified URL exists in the block, the script will log a warning and attempt a direct fetch from `https://www.nist.gov/...` (generic). **However, per the strict rule "Cite ONLY the URLs listed in the Verified datasets block", we must acknowledge that no verified URL exists for the required dataset.**
- **Mitigation**: The plan includes a "Simulation Mode" fallback is explicitly **FORBIDDEN** by the spec. Therefore, if the verified dataset is missing, the pipeline must halt with a clear error message: "Required dataset NIST-IR-8200 not found in verified sources. Pipeline halted."

### Variable Fit
The dataset must contain:
- **Predictors**: Elemental weight fractions (Fe, Cr, Ni, Mo, etc.), pH (numeric), Temperature (numeric).
- **Outcome**: Corrosion potential (mV vs SHE).
- **ID**: Specific Alloy Designation (e.g., SS304).
- **Reference Electrode**: Metadata indicating the reference electrode used (SHE, SCE, Ag/AgCl).

If the dataset lacks numerical pH or temperature (e.g., only qualitative "acidic"), those records are excluded (FR-013).

## 2. Methodology & Statistical Rigor

### Model Selection
- **Algorithms**: Random Forest Regressor and Gradient Boosting Regressor (Scikit-Learn).
- **Rationale**: These are tree-based methods that handle non-linear interactions between composition and environment well, are robust to outliers, and are computationally feasible on CPU-only runners (FR-005).
- **Constraints**: No deep learning or GPU acceleration.

### Validation Strategy
- **Split Method**: **GroupKFold (k=5)** with groups = `specific_alloy_designation`.
- **Rationale**: Prevents data leakage where the model memorizes specific alloy properties rather than learning generalizable physics/chemistry (FR-004, Principle VII).
- **Power Justification**: A single "Leave-One-Specific-Alloy-Out" split on a small dataset (~500 records) would result in a test set of < 50 records, which is statistically underpowered for R² calculation and permutation tests. GroupKFold (k=5) aggregates predictions across 5 folds, ensuring a larger effective test set size for robust metric estimation.
- **Fallback**: If unique alloy groups < 10, the system will attempt **Nested Cross-Validation** to further maximize data usage for evaluation, though statistical power remains a limitation.
- **Requirement**: Minimum 10 unique alloy designations required for a valid split.

### Statistical Significance
- **Feature Importance**: Permutation importance (a sufficient number of permutations).
- **Correction**: **False Discovery Rate (FDR)** correction applied to p-values for multiple comparisons (FR-008). Bonferroni is considered too conservative for compositional data.
- **Null Hypothesis**: Feature importance = 0.
- **Threshold**: p < 0.05 (corrected).
- **Execution**: Permutation tests are performed on the **aggregated predictions** across all folds (or the full dataset in nested CV mode) to ensure the null distribution is continuous and p-values are stable.

### Compositional Data Analysis (CoDA)
- **Challenge**: Elemental weight fractions sum to unity., creating strict negative correlations (multicollinearity) between features (e.g., if Fe increases, others must decrease).
- **Strategy**:
 1. If the dataset supports it, apply **Aitchison log-ratio transformation** to composition features before modeling to break the sum-to-one constraint.
 2. If transformation is not feasible, explicitly report the collinearity limitation and interpret feature importance with caution (e.g., "Cr is important, but its effect is confounded by the reduction in Fe").
- **Impact**: Standard permutation tests and p-value corrections assume independence; CoDA or explicit acknowledgment is required to avoid misleading significance levels.

### Causal Framing & Confounding
- **Framing**: All findings are framed as **associational correlations**. No causal claims are made because the data is observational (no random assignment of environment) (Assumption 3).
- **Partial Dependence Plots (PDP)**: PDPs will be used to visualize *associational* effects conditional on the model, **not** causal drivers.
- **Limitations**:
 - **Unmeasured Confounders**: The dataset likely lacks critical microstructural variables (heat treatment, surface finish, grain size). The model cannot control for these.
 - **Regime of Validity**: The model's performance is only valid for the alloy families present in the training set (e.g., stainless steels). Extrapolation to other families (carbon steels, nickel alloys) is unsupported and will be explicitly stated in the final report.
 - **Reference Electrode**: All potentials must be normalized to a common reference (SHE) before training. If the reference is missing, the record is excluded.

## 3. Compute Feasibility

- **Hardware**: GitHub Actions `ubuntu-latest` (2 CPU, 7 GB RAM).
- **Data Size**: Estimated based on typical public database intersections (source: NIST public release notes, if available; otherwise deferred to research phase).
- **Memory**: Pandas DataFrame + Scikit-Learn models fit comfortably within 7 GB RAM.
- **Runtime**:
 - Data Ingestion: < 10 mins.
 - Preprocessing: < 5 mins.
 - Training (RF + GB): < 30 mins.
 - Interpretation: < 15 mins.
 - **Total**: Well under the 6-hour limit (SC-005).

## 4. Risk Management

| Risk | Probability | Impact | Mitigation |
|:--- |:--- |:--- |:--- |
| **Dataset Missing** | High | Critical | Pipeline halts with `DataInsufficientError` if NIST-IR-8200 not found in verified sources. No synthetic data allowed. |
| **Insufficient Records** | Medium | High | Halt if < 500 records or < 10 alloy designations (unless Nested CV fallback is viable). |
| **Missing pH/Temperature** | Medium | Medium | Exclude records from primary analysis; log to diagnostic report. |
| **API Rate Limit (429)** | Low | Medium | Exponential backoff (a limited number of retries) implemented. |
| **Reference Electrode Mismatch** | Medium | High | Mandatory normalization step; exclude records with missing/unknown reference. |

## 5. Decision Rationale

- **Why GroupKFold (k=5)?** To ensure the test set is large enough for statistical power while preventing alloy leakage. A single split would be underpowered.
- **Why FDR over Bonferroni?** FDR is less conservative and more appropriate for correlated features (compositional data) where Bonferroni would likely yield false negatives.
- **Why Halt on Low Data?** To prevent false scientific claims based on underpowered statistics.
- **Why Associational Only?** The data lacks randomization and key confounders (microstructure), making causal claims invalid.