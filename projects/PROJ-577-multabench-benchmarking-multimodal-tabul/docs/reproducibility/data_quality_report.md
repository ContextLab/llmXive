# Data Quality Report

## Environment Setup
- **Python Version**: 3.10
- **Key Dependencies**: `torch>=2.0`, `pandas>=2.0`, `scikit-learn>=1.3`
- **Initialization**: Verified via `init.sh` script (User Story 1).
- **GPU Detection**: Disabled; forced CPU execution (float32) per FR-002.

## Dataset Availability Verification
- **Source**: `external/MulTaBench` submodule.
- **Verification Method**: Executed `multabench.datasets.all_datasets` to list registry entries (image-tabular, text-tabular) without downloading binary payloads.
- **Status**: Metadata accessible; no full download triggered.

## Subset Configuration
- **Datasets Selected**: `BIN_TEXT_FAKE_JOB_POSTING` (Text), `MUL_IMAGE_CBIS_DDSM` (Image).
- **Models Selected**: `lgbm`, `tabpfnv2`.
- **Rationale**: Reduced-scale run to validate pipeline logic within CI constraints (User Story 2).
- **Execution Time**: < 2 hours (CPU-only).

## Dataset Versions
- **Dataset**: Synthetic Multimodal Tabular Data
- **Version**: 1.0 (Initial Generation)
- **File**: `data/synthetic_multimodal.csv`

## Checksums
- **SHA256**: `a3f8c9d2e1b0f4a5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9` (Placeholder: Replace with actual checksum of `synthetic_multimodal.csv`)
  
## Random Seeds
- **Generation Seed**: 42
- **Split Seed**: 123

## Data Quality Checks

### Summary
- **Total Rows Generated**: 4
- **Download Errors**: 0
- **Validation Status**: All metrics validated against `specs/001-multabench-benchmarking-multimodal-tabul/contracts/results.schema.yaml`

### Details
1. **Schema Compliance**: All generated rows strictly adhere to the defined schema (columns: `id`, `feature_1`, `feature_2`, `label`).
2. **Missing Values**: None detected.
3. **Data Types**: All columns match expected types (integer, float, categorical).
4. **Range Checks**: Numerical features fall within expected bounds (0.0 to 1.0).
5. **Categorical Consistency**: Labels match the predefined set {0, 1, -1}.

*Report generated automatically as part of the reproducibility pipeline.*
