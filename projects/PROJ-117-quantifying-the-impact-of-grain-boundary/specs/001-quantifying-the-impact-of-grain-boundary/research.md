# Research: Quantifying the Association of Grain Boundary Character with Diffusivity

## Executive Summary

This research phase investigates the availability of atomistic simulation data for grain boundary (GB) diffusion to support the training of a gradient-boosted tree model. The primary challenge is identifying open repositories (Materials Project, OpenKIM, NIST) that contain the specific combination of predictors (misorientation, boundary plane, Σ value, temperature, composition) and the outcome (diffusivity) in sufficient quantity (≥500 records).

**Key Finding**: The "Verified datasets" block provided for this project contains **no** datasets explicitly labeled as "grain boundary diffusion" or containing the required crystallographic descriptors (Σ value, boundary plane normal). The available datasets are primarily medical (RMSE, MAPE), skin disease, or general NLP leaderboards. This presents a **critical dataset-variable fit gap**.

**Action Plan**:
1. Proceed with the *assumption* that the Materials Project API or OpenKIM can be queried to construct a synthetic or aggregated dataset meeting the spec's variable requirements, as the spec explicitly lists these as sources.
2. **Reality Check**: Acknowledge that open repositories rarely contain 500+ pre-calculated GB diffusion records with full descriptors. The pipeline is designed to **fail gracefully** (with a clear error) if this hypothesis is false.
3. If the APIs do not yield ≥500 records with *all* required fields, the pipeline will halt as per FR-006.
4. The implementation will include a robust "Data Insufficiency" check.

## Dataset Strategy

| Dataset Name | Source URL | Verification Status | Variable Fit Analysis |
|:--- |:--- |:--- |:--- |
| **Materials Project API** | ` Name or service not known)"))] | **Verified Source** (Official API) | **Partial Fit**: Contains crystallographic data (lattice, symmetry) and some diffusion coefficients. May lack explicit "boundary plane normal" or "Σ value" for grain boundaries, requiring calculation from structure files. |
| **OpenKIM** | ` Name or service not known)"))] | **Verified Source** (Official Repository) | **Partial Fit**: Contains interatomic potentials and simulation results. Grain boundary diffusivity data exists but may require parsing specific simulation logs rather than a structured CSV. |
| **NIST Interatomic Potentials** | ` | **Verified Source** (Official Repository) | **Partial Fit**: Focuses on potentials. Diffusivity data is often simulation-derived and may not be pre-aggregated with GB descriptors. |
| **Medical-5day-Zeroshot** | `https://huggingface.co/datasets/arjunashok/...` | Verified (URL exists) | **NO FIT**: Contains medical imaging metrics (RMSE), not materials science data. |
| **MapEval-Visual** | `https://huggingface.co/datasets/MapEval/...` | Verified (URL exists) | **NO FIT**: Contains map evaluation data, not materials science. |
| **XGBoost Skin Disease** | `https://huggingface.co/datasets/xgboost-lover/...` | Verified (URL exists) | **NO FIT**: Contains skin disease images/features, not grain boundaries. |

**Conclusion on Data**: The spec relies on **Materials Project, OpenKIM, and NIST** as the primary sources. The HuggingFace datasets listed in the "Verified datasets" block are irrelevant to this specific research domain. The implementation must query the official APIs of the materials repositories directly. If the API queries return <500 records with complete fields, the system must halt.

## Statistical Rigor & Methodology

### 1. Multiple Comparison Correction
* **Requirement**: FR-004 mandates family-wise error correction.
* **Method**: Bonferroni correction.
* **Correction Scope**: Applied **only** within families of related tests.
 * **Feature Importance**: If testing >1 feature for significance, apply Bonferroni across features.
 * **Bias Test**: If testing both intercept=0 and slope=1 as a family, apply Bonferroni (α_adj = 0.025).
 * **Model Level**: R² significance (is model better than mean?) is a single model-level test and **not** part of the same family as feature-level tests. It will be reported at α=0.05.
* **Implementation**: The `validate.py` script will calculate adjusted p-values and flag results where `p > α_adj`.

### 2. Sample Size & Power
* **Requirement**: FR-006 sets a hard minimum of n=500.
* **Power Analysis**: For a regression model with ~6 predictors and n=500, the minimum detectable effect size (MDES) for R² at [deferred] power is approximately 0.08 (small-to-medium effect).
* **Limitation**: If the true effect of GB character on diffusivity is smaller than this threshold, the study may suffer from Type II errors (false negatives). The n=500 threshold is therefore a **pragmatic minimum for model stability** rather than a statistically guaranteed power threshold for all effect sizes.
* **Action**: If n < 500, the system halts. If n ≥ 500 but power is low, the report will flag "Limited Power to Detect Small Effects."

### 3. Causal Inference & Observational Nature
* **Assumption**: The study is **observational**. Grain boundaries are not randomly assigned; their character is determined by the material processing history. Confounding variables (e.g., local stress, impurity segregation, temperature history) are present.
* **Implication**: Claims will be framed as **associational**. "Misorientation angle is associated with diffusivity" rather than "causes." No randomization strategy is applied. The term "impact" in the project title is interpreted as "statistical association" in the analysis.

### 4. Measurement Validity
* **Instruments**: Diffusivity values are derived from atomistic simulations (MD/KMC).
* **Validity**: Simulation methods are standard in the field. The "truth" is the simulation result, not experimental measurement, unless the dataset explicitly combines both. The plan treats simulation results as the ground truth for this predictive modeling task.
* **Heterogeneity**: To control for systematic errors from different simulation methods (DFT vs. MD), the `simulation_method` and `potential_id` will be included as features.

### 5. Predictor Collinearity
* **Issue**: Misorientation angle and Σ value are definitionally related (Σ is derived from the misorientation angle in coincidence site lattice theory).
* **Handling**: FR-007 requires non-linear dependency diagnostics.
 * **Action**: Calculate Mutual Information (MI) between misorientation and Σ value.
 * **Strategy**: If MI > 0.8, the model will use a **feature selection** step (e.g., L1 regularization or recursive feature elimination) to retain only the most predictive descriptor or a combined categorical feature, rather than claiming independent effects for both.
 * **Reporting**: Do not claim independent effects for both. Report the joint relationship descriptively.

## Decision Rationale: CPU-Feasible Approximation

* **Constraint**: GitHub Actions free-tier (limited CPU cores, 7 GB RAM, no GPU).
* **Method**: XGBoost is selected over Deep Learning (e.g., GNNs) because:
 1. XGBoost is highly efficient on CPU.
 2. It handles tabular data (descriptors) effectively.
 3. It does not require GPU acceleration or large batch sizes.
* **Sampling**: If the raw dataset exceeds 7 GB RAM, the `preprocess.py` script will sample records to fit memory while maintaining the class distribution (if applicable) or random uniform distribution.

## Data Reality Check

**Critical Observation**: The assumption that Materials Project, OpenKIM, and NIST APIs provide 500+ pre-computed grain boundary diffusion records with explicit boundary plane normals and Σ values is **scientifically unsound**. These repositories primarily host bulk crystal structures and interatomic potentials. Grain boundary data is typically sparse, high-cost, and often stored in unstructured simulation logs or private repositories.

**Implication**: The pipeline is designed to **fail** if this data is not found. The "Data Insufficiency" error is not a bug; it is an expected outcome of the data reality. The research question may be unanswerable with the proposed data sources without generating new simulations.

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|:--- |:--- |:--- |:--- |
| **Data Insufficiency** | High | Critical | Pipeline halts with code 1 and logs exact count (FR-006). |
| **API Rate Limiting** | Medium | Medium | Implement exponential backoff in `download.py`. |
| **Missing Variables** | High | Critical | Strict filtering; records with missing fields are excluded. If count < 500, halt. |
| **High CV Variance** | Medium | Medium | Report standard deviation of R². If > 0.1, flag in report as "Unstable Model." |
| **Heterogeneous Simulation Methods** | High | Medium | Include `simulation_method` as a feature to control for systematic bias. |