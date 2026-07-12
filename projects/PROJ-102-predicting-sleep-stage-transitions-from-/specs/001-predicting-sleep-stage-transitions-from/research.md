# Research: Predicting Sleep Stage Transitions from Scalp EEG Using Deep Learning

## Overview

This research phase establishes the dataset strategy, methodological justification, and feasibility analysis for the implementation plan. It confirms that the Sleep-EDF SC subset contains the necessary variables (Fpz-Cz EEG, hypnogram annotations) and defines the statistical and modeling approaches within the strict CPU-only, 6-hour runtime constraints.

## Dataset Strategy

The primary dataset is the **Sleep-EDF Expanded Database (SC subset)**, available via PhysioNet. This dataset provides single-channel EEG (Fpz-Cz) and hypnogram annotations for a cohort of subjects, which is sufficient for the required transition analysis.

| Dataset Name | Source URL | Variables Required | Verification Status | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **Sleep-EDF SC** | ` | Fpz-Cz EEG (100Hz/128Hz), Hypnogram (30s stages) | **Verified** | Contains exactly the required single-channel EEG and manual sleep stage annotations. |
| **EOG/EMG (Validation)** | ` | EOG (EOG left/right), EMG (submental) | **Verified** | Available in the same dataset for FR-010 validation of features against independent physiological markers. |

**Dataset Fit Confirmation**:
- **Predictor**: Fpz-Cz EEG is present.
- **Outcome**: Hypnogram stages (Wake, N1, N2, N3, REM) are present, allowing transition detection.
- **Validation**: EOG/EMG channels are present in the SC subset, satisfying FR-010.
- **Gap Analysis**: No gaps. The dataset contains all required variables. The "transition windows" (60s) are derived from the hypnogram annotations, which are part of the dataset.

## Methodological Rationale

### 1. Preprocessing Pipeline (FR-002, FR-003)
- **Linear Interpolation**: Applied first to handle missing data/artifacts as per US-1. This is standard for EEG before filtering to avoid filter ringing on gaps.
- **Bandpass (0.5–45 Hz)**: Removes DC drift and high-frequency noise (EMG, line noise harmonics) while preserving sleep-relevant bands (Delta, Theta, Alpha, Sigma, Beta).
- **Notch (50/60 Hz)**: Specifically targets line noise. The [deferred] reduction requirement (US-1) is achievable with a standard IIR notch filter.
- **Segmentation**: Fixed-length epochs for stable states; Fixed-duration windows centered on hypnogram changes. This aligns with the AASM standard and the specific requirement to capture transition dynamics.

### 2. Feature Extraction & Statistical Testing (FR-004, FR-005)
- **Features**:
 - *Time-domain*: RMS, Zero-crossings (simple, low compute).
 - *Frequency-domain*: Absolute/Relative power in standard bands (Delta, Theta, Alpha, Sigma, Beta).
 - *Non-linear*: Sample Entropy, Detrended Fluctuation Analysis (DFA) (captures complexity changes in transitions).
- **Statistical Test**: **Cluster-Based Permutation Test** (Maris & Oostenveld, 2007).
 - *Rationale*: EEG data is temporally autocorrelated. Standard t-tests inflate Type I error. Cluster-based tests control for this by clustering adjacent time/frequency points.
 - *Correction*: **False Discovery Rate (FDR)** (Benjamini-Hochberg, q ≤ 0.05) applied to the cluster-level p-values to control for multiple comparisons across features.
 - *Class Imbalance Handling*: To address the rarity of transition windows, the permutation test will use a **stratified permutation scheme** to preserve the class ratio in each permutation, preventing spurious significance due to imbalance.
- **Validation (FR-010)**: Features will be correlated with EOG/EMG power (e.g., REM vs. NREM differences in EMG tone) to ensure they reflect physiology, not just annotation artifacts. **Crucially**, this validation will be performed on the **pre-transition** features to ensure they predict the *onset* of the physiological state change, not the post-transition label.

### 3. Model Architecture & Training (FR-006, FR-007)
- **Architecture**: **1D-CNN** (Lightweight).
 - *Constraints*: ≤100k parameters.
 - *Design*: 2-3 convolutional layers with small kernels (e.g., 5-10 samples), followed by global average pooling and a single dense output layer.
 - *Rationale*: CNNs are effective at capturing local temporal patterns (spectral shifts) in EEG. 1D-CNNs are computationally cheap on CPU.
- **Input**: Sequences of 3 epochs (90s) **ending 30s before** the transition label.
 - *Temporal Separation*: The model predicts "Will a transition occur in the next 30s?" based on the preceding 90s. This ensures the model learns **pre-transition precursors** and avoids tautological validation where the model simply learns the annotation boundary.
- **Training**:
 - *Optimizer*: Adam (default).
 - *Loss*: Binary Cross-Entropy (Transition vs. No-Transition).
 - **Regularization**: To prevent overfitting on the small N, the model will use **Dropout (0.5)** and **L2 Weight Decay (1e-4)**.
 - **Data Augmentation**: To increase effective sample size, we will apply mild noise injection and time-warping to the training set.
 - *Validation*: **Leave-One-Subject-Out (LOSO)** cross-validation. This ensures the model generalizes to completely unseen subjects, which is critical for wearable applications.
 - *Baseline*: Random baseline (proportion of transitions in training set). Target: Improved accuracy.
- **Fallback Strategy**: If the feature-based model fails to converge or shows no improvement over baseline, the pipeline will fall back to a **raw signal CNN** that learns features directly from the preprocessed EEG, bypassing the univariate statistical filter.

## Compute Feasibility Analysis

| Component | Estimated Resource Usage | Feasibility on GH Actions (2 CPU, 7 GB RAM) |
|:--- |:--- |:--- |
| **Data Download** | Moderate size | **Yes** (Fast, minimal RAM) |
| **Preprocessing** | Moderate RAM (streaming) | **Yes** (Filtering is linear complexity) |
| **Feature Extraction** | Moderate RAM (matrix ops) | **Yes** (Scipy/NumPy are CPU-optimized) |
| **Statistical Testing** | ~3 GB RAM (permutation loops) | **Yes** (Parallelizable, but sequential is fine for <500 clusters) |
| **Model Training** | ~4 GB RAM (batch size 32) | **Yes** (100k params is tiny; <1 hour training time per LOSO fold) |
| **Total Runtime** | ~3-4 hours | **Yes** (Well within 6-hour limit) |

**Risk Mitigation**:
- *Memory*: If peak RAM exceeds 7 GB, data will be processed in smaller subject batches.
- *Time*: If training exceeds a significant duration, the number of permutations in the statistical test will be reduced or the model epochs reduced.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Addressed via Cluster-Based Permutation + FDR correction.
- **Power Analysis**: The dataset (~40 subjects) is small. We acknowledge a **power limitation** for detecting subtle effects. Results will be framed as "associational" and "preliminary" unless effect sizes are large.
- **Causal Inference**: This is an **observational** study (no intervention). Claims will be strictly correlational (e.g., "features associated with transitions").
- **Collinearity**: Frequency bands (Delta, Theta, etc.) are definitionally related (sum to total power). We will report **relative power** to mitigate collinearity and acknowledge the limitation in the discussion.
- **Measurement Validity**: Sleep-EDF annotations are the gold standard (expert scored). EOG/EMG validation provides an independent physiological check.
- **Temporal Independence**: The model input is temporally separated from the target label (30s gap) to ensure the prediction is of a physiological precursor, not the annotation artifact.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use Sleep-EDF SC** | Only dataset with verified Fpz-Cz + Hypnogram + EOG/EMG in one source. |
| **1D-CNN vs. LSTM** | 1D-CNN has fewer parameters, faster CPU training, and sufficient capacity for local spectral patterns. |
| **Cluster-Based Permutation** | Necessary to handle temporal autocorrelation in EEG without arbitrary windowing. |
| **Subject-Level Split (LOSO)** | Prevents data leakage; ensures model generalizes to new subjects, not just new epochs of the same subject. |
| **Pre-Transition Prediction** | Critical to avoid tautological validation; ensures the model predicts the *onset* of a transition, not the label itself. |
| **Decoupled Feature Selection** | Statistical tests are exploratory; model uses full feature set or raw signal to avoid underpowered filtering. |
