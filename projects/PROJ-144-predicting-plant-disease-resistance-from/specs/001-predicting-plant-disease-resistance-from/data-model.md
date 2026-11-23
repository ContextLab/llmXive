# Data Model: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

## Entity Definitions

### 1. MetaboliteProfile
Represents the pre-challenge metabolite abundances for a single sample.
*   **Attributes**:
    *   `sample_id` (str): Unique identifier for the sample.
    *   `inchikey` (str): InChIKey of the metabolite.
    *   `intensity` (float): Raw intensity value (log-transformed during preprocessing).
    *   `study_id` (str): Source study identifier (for batch correction).
    *   `timestamp` (datetime): Time of sample collection (to verify pre-challenge status).

### 2. ResistanceLabel
Represents the disease-resistance phenotype for a sample.
*   **Attributes**:
    *   `germplasm_id` (str): Identifier for the plant variety.
    *   `assay_score` (int/float): Raw assay score (binary 0/1 or ordinal 0–3).
    *   `measurement_method` (str): Method used for resistance assay (e.g., "leaf spot", "wilt").
    *   `harmonized_score` (float): Z-scored score (used ONLY for ordinal exploratory analysis).
    *   `binary_label` (int): 1 (Resistant) or 0 (Susceptible). **Used for Random Forest training and validation.**

### 3. ModelArtifact
Represents the trained Random Forest classifier and its metadata.
*   **Attributes**:
    *   `model_id` (str): Unique hash of the model configuration.
    *   `feature_importances_` (dict): Mapping of metabolite ID to importance score.
    *   `balanced_accuracy` (float): Performance metric on hold-out set.
    *   `roc_auc` (float): ROC-AUC score.
    *   `vif_scores` (dict): Mapping of metabolite ID to VIF score.
    *   `permutation_p_value` (float): Significance against null distribution.

## Data Flow

1.  **Raw Input**: `data/raw/intensity_table.csv`, `data/raw/phenotype_metadata.csv`
2.  **Preprocessing**:
    *   Filter missing values (>30%).
    *   Log-transform.
    *   Align by InChIKey.
    *   Apply ComBat (if >1 study).
3.  **Label Harmonization**:
    *   If `assay_score` is binary: map to `binary_label` (0/1). **Do not z-score.**
    *   If `assay_score` is ordinal: compute `harmonized_score` (z-scored). `binary_label` is derived by thresholding `assay_score` (e.g., >1.5 = Resistant).
4.  **Model Training**:
    *   Input: `binary_label` (categorical) for Random Forest.
 * Split: Train ([deferred]), Hold-out ([deferred]) if N ≥ 50.
    *   Feature Selection: Within CV folds only.
    *   Train: Random Forest.
5.  **Evaluation**:
    *   Metrics: `results/metrics.json` (using `binary_label`).
    *   Diagnostics: `results/shap_analysis.json` (VIF, Correlations).
    *   Interpretation: `results/pathway_analysis.json`.

## Schema Definitions (Contracts)

See `contracts/` directory for formal YAML schemas:
*   `contracts/dataset.schema.yaml`: Defines structure of `batch_corrected_matrix.csv` and `labels.csv`.
*   `contracts/metadata.schema.yaml`: Defines structure of `results/metrics.json` and `results/shap_analysis.json`.
*   `contracts/output.schema.yaml`: Defines structure of `results/pathway_analysis.json` and `results/plots/*.png`.

## Data Constraints

*   **Missing Values**: Features with >30% missingness are dropped.
*   **Normalization**: All intensities must be log-transformed before modeling.
*   **Batch Correction**: ComBat applied only if `study_id` has >1 unique value.
*   **Label Harmonization**: `binary_label` is used for RF training. `harmonized_score` is optional for exploratory analysis.
*   **Independence**: Test set must not be used in any feature selection or hyperparameter tuning.