# Research: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Scientific Rationale

The core hypothesis posits that individual differences in resting-state and task-related neural oscillations (specifically in the alpha and beta bands) serve as a biomarker for responsiveness to anodal tDCS over the primary motor cortex (M1). While tDCS is widely used for motor rehabilitation, inter-subject variability in response is high. Identifying pre-stimulation EEG signatures could enable personalized stimulation protocols.

## Dataset Strategy

The plan relies on verified data sources. However, a critical constraint is **pairing**: the system requires EEG recordings and tDCS motor performance scores for the *same* subjects.

| Dataset | Role | Source URL | Verification Status | Strategy |
|:--- |:--- |:--- |:--- |:--- |
| **PhysioNet (EEG)** | Source of EEG resting-state/task data. | ` | **Verified** | Used for EEG feature extraction. **Note**: This dataset is likely pre-processed. Pipeline will detect this and skip redundant filtering/re-referencing. |
| **OpenNeuro (tDCS)** | **NOT SUITABLE**. | ` | **Verified (but Invalid)** | This dataset contains structural/fMRI data, not tDCS motor performance scores. **Excluded** from Primary Mode. |
| **Synthetic Target (Decoupled)** | Fallback outcome variable for structural validation. | N/A (Generated) | N/A | Generated with random noise (mean=0). Success criterion: R² ≈ 0.0 (±0.05). |
| **Synthetic Target (Positive Control)** | Fallback outcome variable for power validation. | N/A (Generated) | N/A | Generated with known effect size (Cohen's d = 0.5). Success criterion: Model detects signal (R² > 0, p < 0.05). |

**Dataset Fit & Mismatch Analysis**:
- **Primary Mode**: Requires a single dataset containing both EEG and tDCS motor scores for the *same* subjects.
- **Mismatch Scenario**: Public repositories (PhysioNet, OpenNeuro) do not contain such paired data. The OpenNeuro dataset cited is structural/fMRI and lacks the target variable entirely. A direct ID join between PhysioNet and OpenNeuro is statistically impossible due to independent subject pools.
- **Decision**: The pipeline will **immediately enter Fallback Mode** upon detecting the absence of a valid paired dataset. The "Primary Mode" is scientifically unexecutable with current verified sources. No claims of biomarker validity will be made in Primary Mode.

## Methodological Rigor

### Statistical Approach
1. **Feature Extraction**:
 - **Spectral Power**: Welch's method for Delta (1-4Hz), Theta (4-8Hz), Alpha (8-13Hz), Beta (13-30Hz), Gamma (30-45Hz).
 - **Connectivity**: Phase Locking Value (PLV) and weighted Phase Lag Index (wPLI).
 - **Preprocessing**: Band-pass 1–45 Hz (assuming 1 Hz lower bound per FR-003 typo), Common Average Reference (CAR), bad channel rejection via z-score (>3 SD).
 - **Data State Detection**: Check if input data is already pre-processed. If so, skip filtering/re-referencing to avoid artifacts.

2. **Dimensionality Reduction**:
 - Apply PCA or Variance Thresholding to reduce the number of predictors to a manageable subset (approx. a small number of features) before modeling to mitigate the "curse of dimensionality" and overfitting.

3. **Modeling**:
 - **Algorithm**: Ridge Regression (L2 regularization) to handle multicollinearity.
 - **Validation**: 5-fold Cross-Validation.
 - *Outer Loop*: Evaluation (1,000 permutations).
 - *Inner Loop*: Hyperparameter tuning (100 permutations to ensure <6h runtime).
 - **Significance**: Permutation testing to establish a null distribution for R².

4. **Multiple Comparison Correction**:
 - **FDR**: Benjamini-Hochberg procedure applied to p-values of model coefficients.

5. **Sensitivity Analysis (FR-007)**:
 - Sweep significance thresholds (p:, 0.05, 0.1) and R² thresholds (0.2, 0.3, 0.4).
 - **Justified Stability Rule**: The primary finding is "Justified" only if significance holds in **at least 2 out of 3** tested p-thresholds.
 - **Reporting**: Explicitly report the threshold range where significance is lost.

6. **Power Analysis**:
 - Calculate Minimum Detectable Effect Size (MDES) for N=109, alpha=0.05, and the number of predictors.
 - If power < 0.80 for the expected effect size, this limitation is explicitly reported in the final output, and non-significant results are qualified.

### Computational Feasibility (CPU-Only)
- **Memory**: Data will be loaded in chunks. If the full dataset exceeds available system memory, epochs will be subsampled to maintain memory safety.
- **Runtime**: All operations (filtering, FFT, regression) are CPU-tractable.
 - **Optimization**: Inner CV loop permutations reduced to 100 to ensure total runtime ≤ 6 hours on 2 CPU cores.
 - **No GPU**: No CUDA dependencies. `torch` (if used for any auxiliary tasks) will be CPU-only; primary stack is `mne` + `scikit-learn`.

## Assumptions & Risks

- **Assumption**: No verified dataset contains paired EEG and tDCS motor scores. The system defaults to Fallback Mode.
- **Assumption**: The PhysioNet parquet file is pre-processed. The pipeline detects this and skips redundant steps.
- **Risk**: The OpenNeuro dataset cited is structural/fMRI and lacks behavioral scores.
 - **Mitigation**: Explicitly excluded from Primary Mode. System defaults to Fallback Mode.
- **Risk**: Overfitting due to high dimensionality.
 - **Mitigation**: Dimensionality reduction (PCA) applied before modeling.
- **Risk**: Runtime > 6 hours.
 - **Mitigation**: Reduced permutations in inner CV loop; feature subsampling.
- **Risk**: Spec Typos (FR-003 "low-frequency", SC-003 "-hour").
 - **Mitigation**: Plan assumes 1 Hz and 6 hours respectively. A kickback to the spec author is recommended.