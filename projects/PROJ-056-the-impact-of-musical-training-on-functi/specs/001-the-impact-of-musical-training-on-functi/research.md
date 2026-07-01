# Research: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Dataset Strategy

### 1.1 Verified Sources Analysis
The project specification requires data from the **ABCD Study** or **HCP-Adolescents**. The provided "Verified datasets" block has been analyzed:

| Dataset | Status | Verified URL(s) | Notes |
|:--- |:--- |:--- |:--- |
| **ABCD Study** | **UNVERIFIED / INVALID** | ` (and others) | The provided URLs point to generic zip files with names like `fdjis.zip` or `BTS_TaehyungV2_v2_e1110.zip`. These do **not** contain ABCD neuroimaging data. **No verified source found for ABCD.** |
| **HCP-Adolescents** | **NO VERIFIED SOURCE** | N/A | The verified datasets block explicitly states: "NO verified source found". |
| **HCP (General)** | **UNVERIFIED** | ` | These point to "Diffusion-datas" or generic CSVs, not the specific adolescent rs-fMRI and behavioral data required. |

### 1.2 Dataset Fit Assessment
**Critical Finding**: The required variables (resting-state fMRI, years of musical training, age, sex, SES) are **not available** in any verified source provided in the input.
- **Gap**: The spec assumes access to ABCD/HCP-Adolescents. The verified list contains no valid data for this.
- **Impact**: The pipeline cannot execute on real data.
- **Mitigation Strategy**:
 1. The implementation will include a `synthetic_generator.py` module that creates a statistically valid synthetic dataset mimicking the expected distribution of the target study (N=150, 75 per group, correlation structure).
 2. The pipeline will be designed to accept a `data_path` argument. If a valid real dataset is provided later (with verified URLs), the synthetic generator is bypassed.
 3. **Blocking Condition**: If the system attempts to run in `Analysis Mode` without a verified data source, it MUST halt with `Error: Data Source Missing. No verified ABCD/HCP-Adolescents dataset found in provided list.`
 4. **Verification Mode**: Uses synthetic data (including mock NIfTI) to verify code execution, memory constraints, and statistical logic (Null-First). **No scientific results are claimed.**

### 1.3 Variable Mapping (Target vs. Available)

| Required Variable | Source in Spec | Available in Verified Data? | Strategy |
|:--- |:--- |:--- |:--- |
| **Resting-state fMRI** | ABCD/HCP-Adolescents | **No** | Generate synthetic correlation matrices (z-transformed) with known ground truth (Null-First). |
| **Years of Training** | ABCD/HCP-Adolescents | **No** | Generate synthetic distribution (non-musicians at a baseline level, uniform 1-10 for musicians). |
| **Age/Sex/Motion/SES** | ABCD/HCP-Adolescents | **No** | Generate synthetic confounders matched between groups. |

## 2. Statistical Methodology

### 2.1 Group Comparison (FR-003)
- **Method**: Welch's t-test (unequal variances) for each edge in the connectivity matrix.
- **Correction**: Benjamini-Hochberg (FDR) for multiple comparisons (family-wise error control at edge level).
- **Effect Size**: Cohen's d calculated for every connection.
- **Rationale**: Welch's t-test is robust to unequal sample sizes and variances, common in neuroimaging groups. FDR is standard for high-dimensional connectivity data.

### 2.2 Network-Based Statistic (NBS) (FR-008)
- **Method**: Permutation-based NBS.
 1. Threshold primary statistic (t-stat) at an initial level (e.g., p=0.05 uncorrected).
 2. Identify connected components (clusters of edges).
 3. Permute group labels (multiple permutations) to generate null distribution of component sizes.
 4. Calculate FWER-corrected p-value for the largest component.
- **Rationale**: NBS controls for family-wise error at the network component level, offering higher power than edge-wise FDR for detecting distributed network effects.
- **Feasibility**: Permutation tests are CPU-intensive but feasible for N=150 and ~5000 edges (Schaefer 200) within 6 hours on 2 cores if optimized (numpy vectorization).

### 2.3 Correlation Analysis (FR-004)
- **Method**: Pearson correlation (or Spearman if non-normal) between `years_of_training` and connectivity strength (z-score) within the musician group only.
- **Output**: r, p-value, 95% CI, Cohen's q (effect size for correlation).
- **Rationale**: Directly addresses the secondary research question regarding dose-response.

### 2.4 Sensitivity Analysis (FR-005)
- **Method**: Re-run edge-wise significance tests at thresholds p < 0.01, 0.05, 0.10.
- **Output**: Table of significant edge counts and % reduction.
- **Rationale**: Assesses robustness of findings to arbitrary threshold choices.

### 2.5 Power & Sample Size
- **Assumption**: The spec assumes 50-75 subjects per group provides ≥0.80 power for d=0.5.
- **Limitation**: This is an assumption. The implementation will log the actual achieved power based on the sample size and observed variance (post-hoc power) in `research.md` results.
- **Caveat**: If real data yields <50 per group, the system halts (per US-1).

### 2.6 Power Analysis for Network-Based Statistic
- **Problem**: NBS is known to have low power for small sample sizes (N<100 per group) unless effect sizes are very large or spatially extensive.
- **Strategy**:
 1. Implement a **Power Simulation** in `code/analysis/power.py` to estimate the minimum detectable effect size (MDES) for the specific N (75/group) and permutation count (1000).
 2. The simulation will vary the injected effect size and spatial extent to determine the threshold for adequate statistical power.
 3. **Reporting**: If the observed effect size in real data is below the MDES, the result will be flagged as "Underpowered for NBS" and interpreted with caution.

### 2.7 Justification of Dual Inference Strategy
- **Issue**: Functional connectivity matrices are highly correlated (non-independent edges). FDR controls the false discovery rate but does not account for spatial dependency as effectively as NBS.
- **Resolution**:
 - **FDR**: Used for **edge-wise** inference to identify specific connections with high sensitivity, controlling the proportion of false discoveries.
 - **NBS**: Used for **network-level** inference to identify connected components with high specificity, controlling the family-wise error rate for the entire network structure.
 - **Rationale**: These methods answer complementary questions. FDR is sensitive to sparse, strong effects; NBS is sensitive to distributed, weaker effects. The plan uses both to provide a comprehensive view.

### 2.8 Sensitivity to Unmeasured Confounding
- **Problem**: Confound control (matching/regressing) is insufficient to rule out unmeasured confounders (e.g., IQ, general cognitive ability).
- **Strategy**:
 1. Implement a **Confounder Sensitivity Analysis** in `code/analysis/sensitivity.py`.
 2. Instead of E-values (for risk ratios), calculate the **minimum strength of association** an unmeasured confounder would need with both the exposure (musical training) and outcome (connectivity) to explain away the observed effect size (Cohen's d).
 3. **Reporting**: Report the "Confounding Strength" required to reduce the observed effect to zero. If this strength is implausibly high, the result is considered robust.

## 3. Computational Constraints & Feasibility

- **Memory**: 7GB RAM limit.
 - **Strategy**: Connectivity matrices (e.g., 200x200) are small (~320KB). The bottleneck is loading NIfTI files. Since real NIfTI is unavailable, synthetic data avoids this. If real data were used, we would process subjects one-by-one (streaming) to avoid loading all NIfTIs at once.
- **Runtime**: ≤6 hours.
 - **Strategy**: NBS with 1000 permutations on 2 cores is feasible for N=150. If NBS is too slow, the plan allows for reducing permutations to 500 (documented in `research.md`).
- **No GPU**: All operations (correlation, t-test, permutations) use `numpy`/`scipy` which run on CPU.

## 4. Causal Inference & Validity

- **Observational Nature**: This is an observational study. Musical training is not randomized.
- **Claim Limitation**: Findings will be framed as **associational**. "Musical training is associated with..." not "Musical training causes...".
- **Confounding**: Age, sex, motion, and SES are regressed out or matched. However, unmeasured confounders (e.g., IQ, socioeconomic status nuances) remain a limitation.
- **Collinearity**: If "years of training" is highly correlated with "age" (older adolescents have more training), this will be checked. If collinear, independent effects cannot be claimed; only descriptive correlations will be reported.

## 5. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use Synthetic Data (Null-First)** | No verified source for ABCD/HCP-Adolescents exists in the provided list. Pipeline must be testable. Primary test uses NO injected effect to verify Type I error control. |
| **NBS with 1000 Permutations** | Standard for neuroimaging. Feasible within 6h on 2 cores for N=150. Power analysis will be performed to assess detectability. |
| **FDR Correction** | Standard for edge-wise inference. Complements NBS. |
| **Halt on <50 subjects** | Per US-1, to prevent underpowered inference. |
| **Dual Inference (FDR + NBS)** | FDR for edge sensitivity, NBS for topological robustness. Addresses spatial dependency. |
| **Confounder Sensitivity Analysis** | Quantifies robustness to unmeasured confounding, addressing the limitations of simple regression. |
