# Data Model: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## 1. Entity Relationship Overview

The data flow consists of:
1.  **Raw Data**: OQMD subset (Parquet/CSV) containing composition, structure, and targets.
2.  **Processed Data**: Cleaned, split (Train/Val/Test), and PCA-transformed features.
3.  **Model Artifacts**: Saved checkpoints for Baseline, Ensemble, MC-Dropout, and Sparse GP.
4.  **Prediction Data**: CSVs containing predictions, bounds, and variance for each method.
5.  **Evaluation Data**: Metrics (ECE, Interval Score) and screening results.

## 2. Key Entities & Attributes

### MaterialSample
*Represents a single inorganic compound.*
*   `material_id` (str): Unique identifier.
*   `composition` (dict): Elemental fractions (e.g., `{"Fe": 0.5, "O": 0.5}`).
*   `structural_descriptors` (dict): `atomic_radius`, `packing_fraction`.
*   `formation_energy` (float): Target 1.
*   `bulk_modulus` (float): Target 2.
*   `band_gap` (float): Target 3.
*   `excluded` (bool): True if missing critical features.

### UQPrediction
*Output of a UQ method for a single sample.*
*   `material_id` (str)
*   `method` (str): "ensemble", "mc_dropout", "sparse_gp".
*   `prediction` (float): Point estimate.
*   `lower_bound_50` (float): 50% CI lower.
*   `upper_bound_50` (float): 50% CI upper.
*   `lower_bound_90` (float): 90% CI lower.
*   `upper_bound_90` (float): 90% CI upper.
*   `variance` (float): Predictive variance.
*   `uncertainty_type` (str): "aleatoric", "epistemic", or "total".

### CalibrationMetric
*Evaluation result for a method.*
*   `method` (str)
*   `metric_name` (str): "ECE", "Interval_Score_50", "Interval_Score_90", "Sharpness".
*   `value` (float)
* `confidence_level` (str): "50%", "[deferred]".

## 3. File Specifications

### `data/raw/oqmd_subset.parquet`
*   **Source**: Hugging Face (verified URL).
*   **Format**: Parquet.
*   **Schema**: Matches OQMD standard (columns: `formation_energy_per_atom`, `bulk_modulus`, `band_gap`, `composition`, etc.).

### `data/processed/raw_train.csv`, `raw_val.csv`, `raw_test.csv`
*   **Split**: 80/10/10 stratified by `formation_energy` quantiles.
*   **Columns**: `material_id`, `feature_vector` (array or flattened columns), `formation_energy`, `bulk_modulus`, `band_gap`, `target_bin` (for stratification).

### `data/processed/pca_transformer.pkl`
*   **Type**: Pickled `sklearn.decomposition.PCA` object.
*   **Usage**: Transforms raw features to reduced space for Sparse GP.

### `data/validation_report.json`
*   **Schema**:
    ```json
    {
      "excluded_count": 123,
      "missing_columns": ["packing_fraction"],
      "total_raw_rows": 50000,
      "remaining_rows": 49877
    }
    ```

### `results/predictions/uq_predictions_*.csv`
*   **Columns**: `material_id`, `method`, `prediction`, `lower_bound_50`, `upper_bound_50`, `lower_bound_90`, `upper_bound_90`, `variance`, `uncertainty_type`.

### `results/metrics/calibration_summary.csv`
*   **Columns**: `method`, `metric_name`, `confidence_level`, `value`.

## 4. Data Lineage & Integrity

1.  **Download**: `download.py` fetches data from HF, computes SHA256 checksum, stores in `data/raw/`.
2.  **Validation**: `validation.py` checks for nulls in targets/features, logs to `validation_report.json`, excludes bad rows.
3.  **Split**: `preprocess.py` performs stratified split, saves CSVs.
4.  **Transformation**: `preprocess.py` fits PCA on Train, saves to `pca_transformer.pkl`, transforms Train/Val/Test.
5.  **Training**: Models trained on processed data, saved to `results/models/`.
6.  **Inference**: Predictions generated, saved to `results/predictions/`.
7.  **Evaluation**: Metrics computed from predictions and ground truth, saved to `results/metrics/`.
