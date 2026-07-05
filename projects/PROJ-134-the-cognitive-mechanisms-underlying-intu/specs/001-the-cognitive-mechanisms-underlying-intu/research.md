# Research: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

## 1. Research Question & Hypothesis

**Question**: How does the visual salience of avatars' emotional expressions in immersive virtual environments modulate the activation of specific moral foundations and shape intuitive moral judgments?

**Hypothesis**: High visual salience of emotional expressions will significantly increase the activation of specific moral foundations (e.g., Care, Fairness) and alter intuitive moral judgments compared to low salience conditions, independent of pre-existing trait scores.

**Current Phase Status**: **Pipeline Validation Only**.
Due to the absence of real VR interaction logs and a verified "Moral Stories" dataset, this phase validates the **statistical pipeline** (data ingestion, Bayesian modeling, reporting) using **synthetic data** with a known ground truth. Scientific claims regarding the hypothesis are **deferred** until real data is acquired in Phase 4.

## 2. Dataset Strategy

The study relies on two primary data sources. The plan maps these to the experimental design.

| Dataset Name | Source URL | Role in Study | Variable Mapping | Status |
| :--- | :--- | :--- | :--- | :--- |
| **MFQ (Synthetic)** | *None (Simulated)* | **Predictor/Covariate**: Provides baseline moral foundation scores (Care, Fairness, etc.) based on published norms (Gervais et al., 2011). | `foundation_scores`, `participant_id` | **Simulated** (Validated against norms) |
| **Moral Stories** | *No verified source in block* | **Stimuli**: Text vignettes used as the basis for VR scenes. | `story_text`, `story_id` | **Simulated** (Bypasses URL verification) |
| **VR Interaction Logs** | *None (Simulated)* | **Outcome**: Response times, gaze tracking, judgment ratings. | `judgment_rating`, `response_time`, `gaze_metrics` | **Simulated** (Ground truth defined) |

**Critical Note on Data Sources**:
1.  **MFQ Dataset**: The previously referenced `lukebruhns/identity-refusal-mfq2` dataset is **invalid** for this study as it is synthetic refusal data, not human psychometric data. The plan now uses a **Synthetic MFQ Generator** that samples from a multivariate normal distribution based on the means and standard deviations reported by Gervais et al. (2011) to ensure psychometric validity.
2.  **Moral Stories Dataset**: No verified URL exists in the "Verified datasets" block. The plan **simulates** the vignette data structure locally. This is a **Simulation Bypass** of the Verified Accuracy principle, explicitly noted in the report.
3.  **VR Logs**: No real VR logs are available. The plan **simulates** these logs with a known `ground_truth_effect` (e.g., salience increases judgment by 0.5 points) to validate that the Bayesian model can recover this effect.

## 3. Methodological Approach

### 3.1. Data Ingestion & Experimental Construction (US-1)
1.  **Ingest (Synthetic MFQ)**: Generate synthetic MFQ data using `code/utils/norms.py` based on Gervais et al. (2011) parameters.
2.  **Simulate Stimuli**: Generate a synthetic "Moral Stories" dataframe with `story_id`, `text` (placeholder), and `salience_level` (randomized low/high).
3.  **Simulate Logs**: Generate synthetic `response_time`, `gaze_metrics`, and `judgment_rating` columns. **Crucially**, the `judgment_rating` is generated using a linear model: `rating = beta_0 + beta_salience * salience + beta_foundation * foundation + noise`, where `beta_salience` is a known `ground_truth_effect` (e.g., 0.5).
4.  **VR Mapping**: Explicitly log the mapping of `salience_level` to "blend-shape parameters" in `data/logs`.
5.  **Validation**: Compare the synthetic MFQ distribution against Gervais et al. norms (US-6).

### 3.2. Bayesian Model Execution (US-2)
*   **Model**: Hierarchical Bayesian model using PyMC3 (CPU-optimized).
*   **Likelihood**: Gaussian (for continuous judgment ratings).
*   **Priors**: Normal priors for coefficients (weakly informative).
*   **Predictors**:
    *   Fixed Effect: `salience_level` (Low vs. High).
    *   Covariates (Moderators): `foundation_scores`.
    *   Interaction: `salience_level * foundation_scores`.
*   **Inference**: NUTS sampler.
*   **Convergence**: Check R-hat < 1.05.
*   **Decision Rule**: **Parameter Recovery Check**. Does the 95% credible interval for `beta_salience` include the `ground_truth_effect`?

### 3.3. Model Comparison & Validation (US-3)
*   **Model Comparison**: Calculate AIC and WAIC for the Salience-Augmented Model vs. Baseline.
*   **Validation Goal**: Verify that the model selection procedure correctly identifies the Salience model as better (if `ground_truth_effect` > 0).
*   **Sensitivity Analysis**: Sweep decision threshold over {2, 10, 20}.
*   **Mixed-Effects Regression**: Run as a robustness check, applying Bonferroni correction.

### 3.4. Artifact Hashing & State Update (US-5)
*   **Mechanism**: `code/utils/hashing.py` calculates SHA-256 checksums for all derived files (`data/processed/*.csv`, `data/processed/*.nc`).
*   **Update**: The script updates `state/projects/PROJ-134-.../state.yaml` `artifact_hashes` map.

### 3.5. Psychometric Validation (US-6)
*   **Mechanism**: `code/utils/norms.py` compares the mean and SD of the synthetic MFQ scores against Gervais et al. (2011).
*   **Pass Criteria**: Synthetic mean/SD within 1 SD of published norms.

## 4. Compute Feasibility & Constraints

*   **Hardware**: GitHub Actions Free Tier (2 CPU, ~7GB RAM).
*   **Strategy**:
    *   **No GPU**: All PyMC3 sampling runs on CPU.
    *   **Sample Size**: ~200 participants.
    *   **Precision**: Default float64.
*   **Fallback**: If convergence fails, log failure and report MLE.

## 5. Risk Assessment

*   **Missing Real Data**: The study cannot answer the research question with synthetic data. **Mitigation**: Explicitly label the current output as "Pipeline Validation" and defer scientific claims.
*   **Simulation Bias**: Synthetic data may not capture real-world complexity. **Mitigation**: Use norms-based generation.
*   **Convergence Failure**: **Mitigation**: Sensitivity analysis.