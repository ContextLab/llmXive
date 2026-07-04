# Research: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Function in Aging Using UK Biobank Data

## Dataset Strategy

The analysis relies on the UK Biobank cohort, specifically the subset of participants with linked 16S rRNA sequencing data and cognitive assessment scores.

| Dataset Name | Description | Verified Source / Loader | Variables Required | Fit Check |
| :--- | :--- | :--- | :--- | :--- |
| **UK Biobank Microbiome** | 16S rRNA sequencing data (genus-level) for gut microbiome composition. | **Verified Source**: The `# Verified datasets` block in the prompt does **NOT** contain a URL for UK Biobank microbiome data (it only lists a reasoning dataset). **Action**: The plan mandates using the official `ukbiobank` Python package (requires user credentials) or manual provisioning of the specific "UK Biobank Microbiome Release 1" files. **Data Availability Gate**: If the specific 16S/Cognitive linked subset is not found, the project switches to "Data Availability Study" mode. | Genus-level counts, Sample ID, Sequencing depth | **Critical Gap**: No verified URL in prompt. **Mitigation**: Code halts if data not found; fallback to "Data Availability Study". |
| **UK Biobank Cognitive** | Cognitive test scores: Reaction Time, Numeric Memory, Reasoning. | **Verified Source**: Same as above. Requires official UKB access. | Reaction Time (field 20400), Numeric Memory (field 20002), Reasoning scores, Participant ID | **Critical Gap**: Same as above. |
| **UK Biobank Confounders** | Demographics and lifestyle: Age, Sex, BMI, Diet, Activity, Medication. | **Verified Source**: Same as above. | Age, Sex, BMI, Diet quality, Physical activity, Medication use, Antibiotic use | **Critical Gap**: Same as above. |

**Decision/Rationale**:
The `# Verified datasets` block provided in the prompt **does not contain** a source for UK Biobank microbiome or cognitive data.
*   **Constraint**: The plan **must not** invent a URL or assume the reasoning dataset contains microbiome data.
*   **Rationale**: The study design relies entirely on UK Biobank. Since the verified list is empty for this specific data, the implementation plan must:
    1.  Explicitly state that the data source is **not verified** in the provided list.
    2.  Implement a "Data Availability Gate" in `download.py` that halts execution if the real UK Biobank data is not found/provided manually.
    3.  If the data is missing, the project enters "Data Availability Study" mode, documenting the gap rather than proceeding with invalid data.
 4. **Sampling Strategy**: To fit within the 14GB disk constraint, the analysis will restrict itself to the "UK Biobank Microbiome Release 1" (approx. [deferred]-10,000 samples). If the full cohort is required, a stratified random sample will be taken to preserve power while fitting the box.

## Statistical Methodology

### 1. Data Preprocessing & ILR Transformation
*   **Quality Control**: Filter reads with low quality scores; remove taxa with < 10% prevalence (pre-screening to reduce dimensionality).
*   **Zero Handling**: **Primary Method**: Apply **Bayesian-multiplicative replacement** (using `zCompositions` logic) to handle zeros. This avoids the bias introduced by fixed pseudocounts in low-abundance taxa.
    *   *Sensitivity Check*: A secondary run with a fixed pseudocount of $1 \times 10^{-6}$ will be performed to assess robustness.
*   **Transformation**: Apply Isometric Log-Ratio (ILR) transformation to genus-level relative abundances.
    *   *Rationale*: ILR produces orthonormal coordinates, breaking the sum-to-zero constraint of compositional data, making standard linear regression valid (Constitution Principle VI).
    *   *Method*: Use `skbio.stats.composition.ilr` or equivalent implementation.

### 2. Association Analysis (Regularized Linear Models)
*   **Model Strategy**: Due to high dimensionality (hundreds of taxa) and potential multicollinearity, the plan mandates **Lasso (L1) regularization** for the primary association model.
    *   *Rationale*: Lasso performs feature selection and prevents overfitting when predictors approach sample size. Ridge (L2) will be used as a sensitivity check.
*   **Confounder Control**: Explicitly control for age, sex, BMI, diet quality, physical activity, and medication use (Constitution Principle VII, FR-004).
    *   *Causal Framing*: Diet and Medication are treated as **potential mediators**. The primary model will run *without* them to estimate total effect, and a secondary model *with* them to estimate direct effect. This framing addresses the risk of collider bias/over-control.
*   **Multiple Testing**: Apply Benjamini-Hochberg (BH) correction **separately** for:
    1.  Main effects (Taxon × Cognitive Metric).
    2.  Interaction effects (Taxon × Age_Group × Cognitive Metric).
    *   *Total Tests*: (Prevalent Taxa × 3 Metrics × 2 Tests).
*   **Causality**: All results will be tagged with `causality_claim: false` (FR-008) as the study is observational.

### 3. Interaction Analysis
*   **Model**: $CognitiveScore \sim ILR_{Taxon} \times Age\_Group + Covariates$
*   **Purpose**: Test for age-dependent effects without splitting the sample (preserving power) (FR-006).
*   **Metric**: Interaction p-value ($p_{int}$), corrected via BH.

### 4. Sensitivity Analysis
*   **Over-Control**: Compare effect sizes between the full model (with diet/medication) and a reduced model (without diet/medication) to detect signal masking (FR-010, SC-006).
*   **Threshold Sweep**: Sweep p-value cutoffs $\in \{0.01, 0.05, 0.1\}$ and generate a **Threshold Sweep Report** (CSV/JSON) listing association counts at each threshold (SC-005).

## Power & Sample Size Considerations
*   **Power Analysis Script**: A script will be generated to estimate power given the expected sample size (post-filtering) and effect size.
*   **Minimum Detectable Effect Size (MDES)**: The script will calculate the MDES for the expected N (e.g., N=5,000) to ensure the study is not futile.
*   **Validation (SC-003)**:
    1.  Generate a synthetic dataset with known $\beta=0.1$.
    2.  Run the power script against this synthetic data.
    3.  Verify the script outputs the correct power estimate.
    4.  Generate a **Power Report** before proceeding to real analysis.
*   **Limitation**: If the available sample size is small, the study may be underpowered. This will be explicitly reported in the Power Report.
*   **Collinearity**: ILR transformation addresses compositional collinearity. VIF will be checked for confounders; if VIF > 5, collinearity will be reported.

## Validation & Instrumentation
*   **Cognitive Instruments**: UK Biobank's reaction time, numeric memory, and reasoning tasks are used.
*   **Validation Evidence (FR-009)**: The plan includes a specific task to retrieve and validate the primary validation papers (e.g., Fawns-Richell et al.) before analysis.
*   **Internal Validation**: Since no external cohort exists, the study will perform **k-fold cross-validation** (k=5) to assess model stability and prevent overfitting, acknowledging the limitation that external validation is not possible.

## Risk Assessment
1.  **Data Availability**: The `# Verified datasets` block does not contain UK Biobank data. **Mitigation**: Code will require manual data provisioning or official UK Biobank credentials. If unavailable, the project enters "Data Availability Study" mode.
2.  **Missing Variables**: If the actual UK Biobank release lacks specific confounders, the model will be adjusted to available variables, and this deviation will be documented.
3.  **Compute Constraints**: The analysis is designed for CPU-only, streaming data to fit within 7 GB RAM. Large datasets will be processed in batches or sampled (Release 1).
4.  **Dimensionality**: High number of taxa vs. sample size. **Mitigation**: Pre-screening by prevalence and Lasso regularization.
5.  **Zero Handling Bias**: Fixed pseudocounts can bias results. **Mitigation**: Bayesian-multiplicative replacement is the primary method.