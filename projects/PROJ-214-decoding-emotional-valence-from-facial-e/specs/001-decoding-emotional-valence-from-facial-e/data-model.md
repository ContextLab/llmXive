# Data Model: Decoding Emotional Valence from Facial EMG Patterns with Machine Learning

## 1. Entity Definitions

### 1.1 EMGWindow
Represents a single short-duration segment of EMG data.
*   **Subject ID**: Integer (1–32).
*   **Trial ID**: Integer (1–40).
*   **Window Index**: Integer (0–N).
*   **Time**: Float (seconds relative to stimulus onset).
*   **Muscle Channels**:
    *   `corrugator`: Float array (raw signal).
    *   `zygomaticus`: Float array (raw signal).
    *   `orbicularis`: Float array (raw signal).
*   **Features**:
    *   `corr_rms`, `corr_zcr`, `corr_wamp`, `corr_mav`
    *   `zyg_rms`, `zyg_zcr`, `zyg_wamp`, `zyg_mav`
    *   `orb_rms`, `orb_zcr`, `orb_wamp`, `orb_mav`
*   **Label**: Binary (0 = Negative, 1 = Positive) based on valence score.

### 1.2 ValenceLabel
Derived binary label.
*   **Source**: Self-reported valence score (1–9).
*   **Rule**: `1` if `score >= 5.0`, else `0`.
*   **Sensitivity**: Can be re-derived with thresholds 4.9 or 5.1.

### 1.3 FeatureMatrix
2D NumPy array used for training.
*   **Shape**: `(n_windows, 12)`.
*   **Columns**: `[corr_rms, corr_zcr, ..., orb_mav]`.
*   **Type**: `float32` (to reduce memory footprint).

### 1.4 ModelBundle
A single serialized artifact containing both models trained per fold.
*   **RF_Model**: Trained Random Forest (for prediction, importance, SHAP).
*   **LogReg_Model**: Trained Logistic Regression (for Nagelkerke's R²).
*   **Path**: `data/models/model_bundle.pkl` (saved after `train.py`, loaded by `importance.py` and `validate.py`).
*   **Purpose**: Prevents redundant training of RF and LogReg models, ensuring the runtime constraint is met.

### 1.5 ImportanceScore
Quantitative metric for feature contribution.
*   **Metric**: Permutation importance score (mean decrease in accuracy).
*   **Grouping**: Aggregated by muscle (mean of 4 features per muscle).
*   **Confidence**: 95% CI from bootstrap (1000 iterations).

## 2. Data Flow

1.  **Raw Input**: DEAP-EMG `.dat` or `.csv` files (downloaded).
2.  **Preprocessed**: Filtered, windowed, baseline-corrected signals (in memory, not persisted).
3.  **Feature Matrix**: Extracted features (persisted temporarily per subject).
4.  **Model Artifacts**: Trained RF and LogReg models saved to `data/models/model_bundle.pkl`.
5.  **Results**: Accuracy, R², p-values, Cohen’s d (persisted in `data/results/`).

## 3. Storage Constraints

*   **Raw Data**: ~200 MB (DEAP-EMG zip).
*   **Processed Data**: ~500 MB (if all subjects loaded at once).
*   **Strategy**: Subject-level streaming. Max RAM usage kept < 7 GB by processing one subject, training, logging, and clearing memory before the next.
*   **Model Storage**: `model_bundle.pkl` is ~5 MB. Stored in `data/models/`.