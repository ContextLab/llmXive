# llmXive Quickstart Guide

## Overview

This guide provides a step-by-step walkthrough to set up, run, and validate the llmXive automated science pipeline for the "Wan-Streamer v0.1" follow-up project.

## Prerequisites

- Python 3.9+
- Git
- 16GB RAM (minimum), 32GB recommended
- CPU-only environment (no GPU required)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd llmXive-follow-up-extending-wan-streamer
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Project Structure

```
.
├── code/ # Source code modules
├── data/ # Data artifacts (raw, processed, metrics)
├── docs/ # Documentation
├── contracts/ # Schema definitions and data contracts
├── state.yaml # Pipeline state tracking
└── tasks.md # Task list and execution order
```

## Quick Start

### 1. Initialize Project Structure

Run the setup script to create all required directories:
```bash
python code/setup_project_structure.py
```

### 2. Validate Data Sources

The pipeline checks for Wan-Streamer v0.1 logs or fetches VoxCeleb2 automatically:
```bash
python code/data/validate_logs.py
```

### 3. Run the Full Pipeline

Execute the main quickstart validation script which runs all phases in order:
```bash
python code/tasks/run_quickstart_validation.py
```

This script performs:
- Phase 1: Setup (directory creation, config validation)
- Phase 2: Foundational (data source validation, power analysis)
- Phase 3: User Story 1 (Data Extraction & Preprocessing)
- Phase 4: User Story 2 (Estimator Training)
- Phase 5: User Story 3 (Hybrid Inference Simulation)

### 4. Verify Outputs

After completion, verify key artifacts exist:
```bash
python tests/unit/test_setup_verification.py
```

## Data Contracts and Schema Validation

All data artifacts produced by the pipeline adhere to strict schema contracts defined in the `contracts/` directory. These contracts ensure data integrity across all pipeline stages.

**Schema Documentation**:
- [Raw Extract Schema](../contracts/001-raw-extract-schema.json) - Defines the structure of `data/processed/raw_extract.parquet`
- [Filtered Event Schema](../contracts/002-filtered-event-schema.json) - Defines the structure of `data/processed/filtered.parquet`
- [Sampled Dataset Schema](../contracts/003-sampled-dataset-schema.json) - Defines the structure of `data/processed/sampled_dataset.parquet`
- [Hybrid Output Schema](../contracts/004-hybrid-output-schema.json) - Defines the structure of `data/processed/hybrid_output.parquet`
- [Counterfactual Indices Schema](../contracts/005-counterfactual-indices-schema.json) - Defines the structure of `data/processed/counterfactual_indices.parquet`
- [Model Checkpoint Schema](../contracts/006-model-checkpoint-schema.json) - Defines the metadata structure for `data/models/estimator_checkpoint_final.pt`
- [Power Analysis Schema](../contracts/007-power-analysis-schema.json) - Defines the structure of `data/metrics/power_analysis_*.json`
- [Threshold Configuration Schema](../contracts/008-threshold-config-schema.json) - Defines the structure of `code/config/detection_thresholds.yaml`

To validate data against these contracts, use the validator module:
```bash
python code/utils/validators.py --input <path-to-parquet> --contract <contract-file>
```

## Common Issues

### Memory Limitations
If you encounter memory errors, the pipeline will automatically reduce the sample size. You can manually adjust the budget in `code/config.py`.

### Missing Data Sources
If Wan-Streamer logs are not found, the pipeline will fetch VoxCeleb2 from HuggingFace. Ensure you have internet connectivity or pre-download the dataset.

### Validation Failures
If schema validation fails, check the `data/logs/validation_report.txt` for specific error details.

## Next Steps

- Review [Research Documentation](research.md) for detailed methodology
- Examine [Contract Definitions](../contracts/) for schema specifications
- Run individual user story scripts for targeted analysis

## Support

For issues or questions, refer to the project's issue tracker or contact the maintainers.
