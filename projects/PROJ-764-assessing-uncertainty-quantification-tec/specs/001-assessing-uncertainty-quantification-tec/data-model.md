# Data Model: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## Entity Definitions

### MaterialSample
Represents a single inorganic compound in the dataset.
- `id`: Unique string identifier (e.g., OQMD ID).
- `composition`: Dict of element -> fraction (e.g., `{"Fe": 0.5, "Si": 0.5}`).
- `structural_descriptors`: Dict of computed features (e.g., `{"atomic_radius": 1.2, "packing_fraction": 0.74}`).
- `formation_energy`: Float (eV/atom).
- `bulk_modulus`: Float (GPa).
- `band_gap`: Float (eV).
- `excluded_reason`: String (if excluded during validation).

### UQPrediction
Output of the uncertainty quantification pipeline.
- `sample_id`: Reference to MaterialSample.
- `method`: String (one of: `deep_ensemble`, `mc_dropout`, `sparse_gp`).
- `prediction_mean`: Float (predicted property value).
- `prediction_variance`: Float (total variance).
- `aleatoric_variance`: Float (uncertainty due to noise).
- `epistemic_variance`: Float (uncertainty due to model).
- `uncertainty_type`: String (enum: `aleatoric`, `epistemic`, `total`) - **Required by FR-008**.
- `lower_bound_50`: Float (50% confidence lower).
- `upper_bound_50`: Float (50% confidence upper).
- `lower_bound_90`: Float (90% confidence lower).
- `upper_bound_90`: Float (90% confidence upper).
- `interval_width_50`: Float.
- `interval_width_90`: Float.
- `reconstruction_variance`: Float (specific to Sparse GP, optional for others).

### CalibrationMetric
Evaluation results for a specific method and confidence level.
- `method`: String.
- `confidence_level`: Float (0.5 or 0.9).
- `ece_score`: Float.
- `interval_score`: Float.
- `sharpness`: Float.
- `coverage_percentage`: Float.

## Data Flow

1. **Raw Ingestion**: `data/raw/oqmd.parquet` (or csv) -> Downloaded from verified URL.
2. **Validation**: `code/data/validation.py` checks for nulls in targets and missing structural data. Excluded rows logged to `data/processed/exclusion_log.json`.
3. **Feature Engineering**: `code/data/preprocess.py` computes descriptors, applies PCA (for GP), and splits data (80/10/10 stratified).
   - Output: `data/processed/raw_train.csv`, `raw_val.csv`, `raw_test.csv`.
4. **Model Training**: `code/models/` scripts train models. Checkpoints saved to `results/models/`.
5. **Inference**: `code/main.py` runs inference, generates `results/uq_predictions.csv`.
6. **Evaluation**: `code/eval/calibration.py` computes metrics, generates `results/calibration_report.csv` and `results/reliability_diagrams/*.png`.
7. **Screening**: `code/eval/screening.py` generates `results/screening_precision.csv`.

## Data Constraints & Hygiene

- **Checksums**: All files in `data/raw/` must have a corresponding entry in `data/checksums.json` (SHA-256).
- **Immutability**: Raw data is never modified. All transformations write to new files in `data/processed/`.
- **Missing Data**: Rows with missing `formation_energy`, `bulk_modulus`, or `band_gap` are excluded. A summary is written to `validation_report.json`.
- **Reproducibility**: All splits and random operations use a fixed seed (42, 43, 44).