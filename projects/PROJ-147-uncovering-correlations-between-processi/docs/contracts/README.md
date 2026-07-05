# Data Contracts and Schemas

This directory contains the formal data contracts and schema definitions
for the llmXive research pipeline. These schemas ensure data integrity
throughout the pipeline execution and provide validation rules for
inputs, outputs, and intermediate artifacts.

## Schema Files

### `dataset.schema.yaml`
Defines the complete structure of the processed dataset used for training
and evaluation. Includes:
- Metadata (version, source, sample counts)
- Sample records with processing conditions and texture coefficients
- Feature and target definitions
- Validation rules for alloy families (minimum 3 distinct families)

### `input.schema.yaml`
Defines the structure of input data files (CSV/JSON) ingested by the pipeline.
Supports three types:
- `raw_data`: Original measurements from experiments or literature
- `processed_data`: Cleaned and standardized data after preprocessing
- `synthetic_data`: Physics-based generated data with ground truth

### `model.schema.yaml`
Defines the structure of saved model artifacts and training metadata.
Includes:
- Model hyperparameters
- Training dataset information
- Performance metrics (R², MAE, RMSE)
- Feature importance rankings

### `evaluation.schema.yaml`
Defines the structure of model evaluation reports. Includes:
- Overall and per-target metrics
- Per-alloy-family performance breakdown
- Feature importance analysis
- Validation results (SC-002, SC-004 compliance)
- Sensitivity analysis results

### `prediction.schema.yaml`
Defines the structure of prediction outputs. Includes:
- Predicted texture coefficients for new samples
- Confidence intervals (optional)
- Input warnings for out-of-range values

## Usage

These schemas are used by:
1. **Data Loader (T010)**: Validates input data against `input.schema.yaml`
2. **Data Processor (T011a)**: Ensures processed data conforms to `dataset.schema.yaml`
3. **Model Trainer (T013)**: Saves model artifacts following `model.schema.yaml`
4. **Model Evaluator (T020)**: Generates evaluation reports per `evaluation.schema.yaml`
5. **Predictor (T014)**: Outputs predictions following `prediction.schema.yaml`

## Validation

Schema validation is performed at key pipeline stages:
- Data ingestion: Reject malformed input files
- Preprocessing: Ensure derived features are computed correctly
- Model training: Validate dataset meets minimum requirements (≥50 samples/family)
- Evaluation: Check compliance with success criteria (SC-002, SC-004)

## Schema Versioning

All schema files use semantic versioning (`MAJOR.MINOR.PATCH`):
- `MAJOR`: Breaking changes to structure
- `MINOR`: New fields or optional properties
- `PATCH`: Bug fixes and clarifications

Current version: 1.0.0