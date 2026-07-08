# Research: Decoding Emotional Valence from Facial EMG Patterns with Machine Learning

## 1. Problem Definition

The goal is to determine if facial EMG patterns (corrugator, zygomaticus, orbicularis) can predict emotional valence (positive vs. negative) with statistical significance above chance. The study addresses:
1. **Classification**: Can a model distinguish valence?
2. **Attribution**: Which muscle groups drive the prediction?
3. **Robustness**: Are results stable across valence thresholds?

## 2. Dataset Strategy

### 2.1 Primary Dataset: DEAP-EMG
The standard DEAP dataset (Koelstra et al.) lacks facial EMG channels. This project utilizes the **DEAP-EMG** extension, which contains the required synchronized facial EMG recordings.

* **Source Verification**: The dataset is available via verified HuggingFace mirrors.
* **Verified URL**: `https://huggingface.co/datasets/DEAP-EMG/DEAP-EMG/resolve/main/deap_emg.zip`
 * *Note*: If this specific URL is unavailable, the pipeline will fallback to the verified `DEAP-EMG` collection on HuggingFace.
* **Variables Required**:
 * `emg_data`: Raw EMG signals (channels specifically for corrugator, zygomaticus, orbicularis).
 * `valence_score`: Self-reported valence (1-9 scale).
 * `stimulus_duration`: To define pre-stimulus baseline.
* **Fit Check**: The DEAP-EMG dataset contains the required EMG channels and valence scores. No variable mismatch detected.

### 2.2 Alternative/Supplementary Sources
* **EMG Specific Datasets**: While verified EMG datasets exist (e.g., `jxie/emg`), they lack the synchronized self-report valence scores required for this specific supervised learning task. They are noted for potential future extension but not used for the primary pipeline.
 * *Reference*: `

## 3. Methodological Approach

### 3.1 Signal Preprocessing
* **Filtering**: 10–500 Hz Butterworth band-pass to remove motion artifacts and high-frequency noise; 50 Hz notch filter for powerline interference (FR-002).
* **Segmentation**: 1-second non-overlapping windows aligned with stimulus onset (FR-003).
* **Baseline Correction**: Mean subtraction using the pre-stimulus interval (e.g., 2s prior to stimulus) (FR-003).

### 3.2 Feature Extraction
Four time-domain features per muscle per window (FR-004):
1. **RMS** (Root Mean Square): Amplitude envelope.
2. **ZCR** (Zero Crossing Rate): Frequency proxy.
3. **WAMP** (Willison Amplitude): Change in signal magnitude.
4. **MAV** (Mean Absolute Value): Average amplitude.

Total features: 3 muscles × 4 features = 12 features per window.

### 3.3 Modeling Strategy
* **Predictive Model**: Random Forest (100 trees) for classification accuracy, permutation importance, and SHAP values (FR-005, FR-006).
* **Statistical Model**: Logistic Regression (L2 regularization) specifically for calculating **Nagelkerke’s R²** (FR-007). This metric is mathematically undefined for Random Forests.
* **Validation**: **Nested Leave-One-Subject-Out (LOSO)** Cross-Validation.
 * *Outer Loop*: One subject held out as test set (32 iterations).
 * *Inner Loop*: Hyperparameter tuning (C for SVM/LogReg, max_depth for RF) strictly on the remaining 31 subjects. **Strict Subject-Level Isolation**: No data from the held-out subject is used in the inner loop.
 * *Aggregation*: Window-level predictions are aggregated via **majority voting** to produce a single subject-level prediction for evaluation. This resolves the unit of analysis issue and temporal autocorrelation.

### 3.4 Statistical Validation
* **Null Hypothesis**: Accuracy is not different from label-shuffled baseline.
* **Tests**:
 1. **Permutation Test**: 1000 shuffles to generate null distribution (FR-008).
 2. **Paired T-Test**: Paired t-test between observed accuracies and the null distribution (to satisfy Constitution Principle VII).
* **Effect Size**: Cohen’s d calculated between observed accuracy and null distribution (FR-008).
* **Sensitivity**: Accuracy re-calculated with valence thresholds of 4.9, 5.0, 5.1 (FR-009).

## 4. Compute Feasibility & Constraints

* **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, No GPU).
* **Memory Management**:
 * Data loaded subject-by-subject.
 * Intermediate feature matrices deleted immediately after model training for that subject.
 * Random Forest limited to 100 trees; Logistic Regression limited to L2 regularization.
* **Runtime**: Estimated < 4 hours for full pipeline (32 subjects × parallelized folds).
* **Libraries**: `scikit-learn` (CPU optimized), `scipy`, `numpy`, `joblib`. No `torch`/`tensorflow` required.

## 5. Limitations & Assumptions

* **Causality**: Claims are strictly associational. The DEAP-EMG dataset is observational; no random assignment of muscle activity.
* **Sample Size**: N=32 subjects is small for deep learning but sufficient for classical ML with LOSO. Power limitations acknowledged.
* **Threshold**: Valence threshold of 5.0 is standard but arbitrary; sensitivity analysis mitigates this.
* **Missing Data**: Subjects with missing EMG channels or extreme class imbalance (all same label) will be excluded and logged.
* **Spec Conflict**: The source spec FR-005 requires Random Forest for variance analysis, but Nagelkerke's R² requires Logistic Regression. This plan uses Logistic Regression for that specific metric to ensure scientific validity.