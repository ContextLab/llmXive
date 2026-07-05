# Research: Predicting the Impact of Strain Rate on the Yield Strength of Metals

## Executive Summary

This research validates the feasibility of training machine learning models to predict yield strength as a function of strain rate, alloy composition, and grain size, and compares their performance against established empirical constitutive models (Johnson-Cook, Zerilli-Armstrong). **Due to the absence of verified real-world materials science datasets in the current verified block, this study is restricted to a Physics-Consistent Simulated Data generator.** The goal is to validate the pipeline's ability to recover known physics and to perform a sensitivity analysis on imputation, rather than to claim real-world predictive accuracy.

## Dataset Strategy

### Verified Materials Sources (None Found)
Per the project constraints, no verified materials science datasets (NIST, OpenML) containing yield strength, strain rate, and composition were found in the current verified block.

| Dataset Name | Source URL | Status | Relevance to Spec |
| :--- | :--- | :--- | :--- |
| NIST Materials Data Repository | **NO verified source found** | **NOT AVAILABLE** | **REQUIRED**: Contains tensile test data. |
| OpenML (Materials) | **NO verified source found** | **NOT AVAILABLE** | **REQUIRED**: Contains tensile test data. |
| Materials Project API | **NO verified source found** | **NOT AVAILABLE** | **REQUIRED**: Contains composition data. |

### Active Simulation Source
Since no verified materials sources exist, the pipeline uses a **Physics-Consistent Simulated Data** generator.

| Dataset Name | Source URL | Status | Relevance to Spec |
| :--- | :--- | :--- | :--- |
| **Physics-Consistent Simulated Data** | **Local Generator** | **ACTIVE** | **SIMULATED**: Generates synthetic tensile test data based on Johnson-Cook physics with added noise. |

### Critical Gap Analysis & Resolution
The specification (FR-001) requires ingestion of "tensile test data from public repositories (NIST, OpenML)" containing yield strength, strain rate, and composition. **None of the verified datasets in the current block contain materials science data.**

**Resolution Strategy**:
1.  **Immediate Halt**: The pipeline cannot proceed to modeling without a valid materials dataset.
2.  **Proxy/Alternative Data**: The implementation will use a **Physics-Consistent Simulated Data** generator. This generator creates data based on the Johnson-Cook equation but introduces independent noise to break perfect correlations, ensuring the ML model learns the physics rather than memorizing the generator.
3.  **Fallback**: The project will simulate a "mock" dataset for pipeline testing (as per US-1 acceptance scenario) but will explicitly flag that **no real-world validation is possible** with the current verified dataset list.
4.  **Research Note**: Future iterations must update the "Verified datasets" block with actual sources such as:
    *   NIST Materials Data Repository (Tensile Test Database)
    *   OpenML datasets tagged with "materials" or "physics"
    *   The "MatBench" dataset (if available via a verified loader).

*For the purpose of this plan, we assume a mock dataset generator is used to satisfy the pipeline mechanics, while explicitly noting the lack of real-world data.*

### Physics-Consistent Simulated Data Generator
The generator creates synthetic data with the following properties:
- **Yield Strength**: Calculated using the Johnson-Cook equation with added Gaussian noise.
- **Strain Rate**: Sampled from a log-normal distribution (1e-3 to 1e4 s⁻¹).
- **Composition**: Randomly generated elemental fractions for 10 common elements.
- **Grain Size**: Sampled from a log-normal distribution with **independent noise** added to break the perfect correlation with yield strength. This prevents the ML model from "cheating" by learning the generator's internal correlation rather than generalizable physics.
- **Temperature**: Fixed at 298K for simplicity.
- **Processing History**: Includes a hidden "processing history" variable (e.g., cooling rate) that influences grain size but is not directly used in the Johnson-Cook equation, adding complexity to the imputation task.

## Methodology & Statistical Rigor

### Statistical Approach
1.  **Model Comparison**:
    *   **ML Models**: Random Forest, Gradient Boosting, Ridge Regression.
    *   **Empirical Models**: Johnson-Cook, Zerilli-Armstrong (fitted via `scipy.optimize` minimizing SSE).
    *   **Metric**: R², MAE, RMSE on a held-out test set (stratified by alloy family).

2.  **Multiple Comparison Correction**:
    *   When comparing performance across multiple alloy families or strain rate regimes, **Bonferroni correction** or **Benjamini-Hochberg** procedure will be applied to p-values to control family-wise error rate.

3.  **Power Analysis (Deferred)**:
    *   A formal power analysis (Task 0.5.2) will be conducted once the actual dataset size (N) is known. If N < 1000, the plan will explicitly state that the study is underpowered for detecting small effect sizes.

4.  **Causal Inference**:
    *   This is an **observational** study of experimental data. Claims will be strictly framed as **associational**. No causal claims regarding "strain rate causes yield strength changes" will be made without randomization (which is impossible in this context).
    *   **Limitation**: Grain size and composition are often correlated (e.g., grain refiners). The plan will use **Variance Inflation Factor (VIF)** checks. If VIF > 5, the model will report **combined** effects or use regularization (Ridge) to mitigate multicollinearity, explicitly acknowledging the limitation in interpretation.

5.  **Measurement Validity**:
    *   **Strain Rate**: Standardized to s⁻¹.
    *   **Yield Strength**: Standardized to MPa.
    *   **Grain Size**: Standardized to µm.
    *   **Composition**: Encoded as elemental fraction vectors (sum to 1.0).

## Compute Feasibility

*   **Hardware**: GitHub Actions Free Tier (standard CPU allocation, adequate RAM).
*   **Strategy**:
    *   **No GPU**: All models use CPU-only implementations (`scikit-learn`).
    *   **Sampling**: If the dataset exceeds 50k rows, a stratified sample (50k rows) will be used for hyperparameter tuning to ensure runtime < 6h.
    *   **Memory**: Data processing uses chunked reading for large CSVs. Imputation uses `sklearn.impute.KNNImputer` with `n_neighbors=5` (default) to limit memory overhead.

## Decision Rationale

*   **Why KNN Imputation?**: Chosen over mean/median imputation because composition and grain size are physically correlated with yield strength. KNN preserves local structure in the feature space (US-1).
*   **Why Johnson-Cook/Zerilli-Armstrong?**: These are the industry standard baselines for strain rate sensitivity. Comparing against them validates the ML approach's added value (Constitution VII).
*   **Why Wilcoxon Signed-Rank?**: Non-parametric test chosen because error distributions in materials science are often non-normal (skewed by outliers).

## Limitations of Simulated Validation

*   **Circular Validation**: The model is trained on data generated by the same physics it is expected to learn. This creates a risk of the model simply memorizing the generator's rules.
*   **Mitigation**: The generator introduces **independent noise** to grain size and yield strength to break perfect correlations. The model is evaluated on its ability to recover the *expected* physics (via `contracts/literature_expectations.yaml`) rather than achieving perfect fit.
*   **Baseline Saturation**: Fitting Johnson-Cook on data generated by Johnson-Cook will yield an R² value indicating a strong goodness-of-fit. The comparison metric is adjusted to focus on "Generalization to Noise" and "Extrapolation" rather than raw fit.
*   **Real-World Validity**: No claims of real-world predictive accuracy can be made. The study is limited to pipeline validation and physics consistency checks.

## Validation Distinction

To avoid circular validation, the `contracts/literature_expectations.yaml` contract does not merely check if the model learns the generator's base physics (which is trivial). Instead, it validates:
1.  **Noise Robustness**: The model must recover the underlying physics despite the added Gaussian noise in the generator.
2.  **Extrapolation**: The model must perform reasonably well on strain rates outside the training distribution (e.g., high-strain-rate regimes).
3.  **Non-Trivial Relationships**: The model must detect the influence of "processing history" variables that are not explicitly in the Johnson-Cook equation but affect grain size.

This ensures the model is learning the *underlying* physics, not just memorizing the generator's rules.
