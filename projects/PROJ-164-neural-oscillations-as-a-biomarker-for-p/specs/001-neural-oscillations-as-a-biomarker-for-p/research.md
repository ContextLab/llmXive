# Research: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Dataset Strategy

The project relies on public datasets. Due to the rarity of paired EEG and tDCS outcome data for the same subjects, the system is designed to handle both paired (Primary) and unpaired (Fallback) scenarios.

| Dataset Name | Source URL | Format | Role in Project | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **PhysioNet EEG Motor Movement/Imagery** | `https://physionet.org/content/eegmmidb/1.0.0/` | BIDS/EDF | **Primary Source** for raw EEG data. Contains resting-state and task data. | Verified (Raw EDF). |
| **OpenNeuro tDCS Motor Performance** | `https://openneuro.org/` (Generic) | BIDS | **Primary Source** for tDCS motor performance scores (pre/post). | Verified (Behavioral). **No specific paired dataset found.** |
| **Synthetic Data** | N/A | Generated | **Fallback Source**. Generated if no paired data exists. | N/A (Synthetic). |

**Dataset Fit Analysis**:
*   **PhysioNet**: Contains raw EEG data. *Missing*: tDCS outcomes.
*   **OpenNeuro**: Contains tDCS behavioral outcomes. *Missing*: Paired EEG data for the same subjects.
*   **Conclusion**: It is highly probable that **no paired data** exists in these specific verified sources. Therefore, the system will likely default to **Fallback Mode** (FR-001).
*   **Fallback Strategy**: If pairing is not found, the system generates synthetic tDCS response data based on literature-derived aggregate statistics (Cohen's d = 0.5) as per FR-002. This synthetic data is mathematically decoupled from the EEG features to prevent circular validation.
*   **Primary Mode Feasibility**: The primary hypothesis (EEG predicts tDCS response) is **untestable** with the specific datasets listed unless a third, paired dataset is identified. If no paired dataset is found, the project scope is restricted to **Structural Validation Only** via a Constitution Amendment (Phase 5).

## Statistical Methodology

### Primary Mode (If Paired Data Found)
1.  **Preprocessing**: Band-pass filter (1–45 Hz), common average re-reference, bad channel rejection (z-score).
2.  **Feature Extraction**:
    *   Spectral Power: Delta, Theta, Alpha, Beta, Gamma (Welch's method).
    *   Connectivity: Phase Locking Value (PLV), weighted Phase Lag Index (wPLI).
3.  **Dimensionality Reduction**: Apply PCA to reduce feature space. The number of components is determined by the 'elbow method' on the scree plot, capped at `min(N-1, 50)`.
4.  **Modeling**: Ridge Regression with 5-fold cross-validation and nested hyperparameter tuning (alpha selection).
5.  **Positive Control**: Inject a known synthetic signal into a subset of EEG features and the target variable to verify the model can recover R² > 0 and p < 0.05. This validates the statistical engine's ability to detect signal.
6.  **Validation**:
    *   Permutation testing to establish null distribution.
    *   False Discovery Rate (FDR) correction (Benjamini-Hochberg) for multiple comparisons.
    *   Sensitivity analysis on p-value and R² thresholds.

### Fallback Mode (Unpaired Data - Structural Validation Only)
1.  **Data Generation**:
    *   **Decoupled Target**: Generate synthetic tDCS response variable (Gaussian noise, uncorrelated with EEG).
    *   **Correlated Target (Positive Control)**: Generate a separate synthetic dataset where the target is a known linear function of a subset of EEG features.
2.  **Modeling**: Fit Ridge Regression on both datasets.
3.  **Validation**:
    *   **Decoupling Check**: Verify R² ≈ 0.0 (±0.05) for the decoupled dataset to confirm decoupling (SC-002-FB).
    *   **Positive Control**: Verify R² > 0 and p < 0.05 for the correlated dataset to validate the engine's ability to detect signal.
    *   **No statistical inferences** (p-values, R² significance) are reported for the primary hypothesis.
    *   **Output**: Flagged as "Structural Validation Only".

## Power Analysis & Sample Size
*   **Method**: Pre-study power analysis based on available N (from PhysioNet/OpenNeuro) and expected variance.
*   **Limitation**: The study is observational and exploratory. Sample size is determined by available public data.
* **Gate**: If N < required for [deferred] power to detect the expected effect size (Cohen's d = 0.5), the study will explicitly report this limitation and frame results as **Exploratory** only. This methodology is implemented in Task 0.6 of the plan.

## Statistical Rigor & Constraints

*   **Multiple Comparisons**: FDR correction (Benjamini-Hochberg) applied to all feature-level p-values (FR-006).
*   **Causal Inference**: Claims are strictly associational. No causal claims are made regarding tDCS efficacy based on EEG.
*   **Collinearity**: Spectral bands are not independent. Independent effects will be reported with a caveat regarding collinearity.
*   **Compute Constraints**: All methods selected (Ridge, Welch's, PLV) are CPU-tractable. No GPU required. Data will be subsampled if >7 GB RAM.