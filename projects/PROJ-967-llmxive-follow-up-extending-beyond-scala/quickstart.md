# Quickstart Guide: llmXive Follow-up (Teacher Entanglement vs. Scalar Distillation Loss)

This guide provides step-by-step instructions to reproduce the full research pipeline for the llmXive follow-up project, satisfying Constitution Principle I (Reproducibility).

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- Git (for cloning the repository)
- At least 16GB RAM (recommended for full dataset processing)

## 1. Environment Setup

### Clone and Navigate
```bash
git clone <repository-url>
cd projects/PROJ-967-llmxive-follow-up-extending-beyond-scala
```

### Install Dependencies
Install the required Python packages from the pinned `requirements.txt`:
```bash
pip install -r code/requirements.txt
```

### Verify Installation
Ensure key packages are available:
```bash
python -c "import pandas, numpy, sklearn, scipy, yaml, pytest; print('All dependencies installed.')"
```

## 2. Project Structure Initialization

The project directory structure should already be created by Task T001a. If not, run:
```bash
python code/create_project_structure.py
```

This ensures the following directories exist:
- `data/raw/`
- `data/processed/`
- `code/`
- `tests/`
- `results/`

## 3. Data Acquisition (Task T037)

Download the Z-Reward evaluation dataset. This script attempts to fetch the dataset from verified sources (HuggingFace) and includes a fallback mechanism if the primary source is unavailable.

```bash
python code/download_zreward.py
```

**Output**:
- `data/raw/zreward_dataset.parquet` (or similar filename based on the download)
- `data/raw/checksum.txt` (for integrity verification)

*Note: If the download fails, the script will attempt to generate a synthetic dataset with the correct schema to allow the pipeline to proceed, though results will be synthetic.*

## 4. Schema Discovery and Validation (Task T038)

Validate the downloaded dataset against the expected schema and update the schema contract if necessary.

```bash
python code/schema_discovery.py
```

**Output**:
- `specs/001-llmxive-entanglement-analysis/contracts/dataset.validated.schema.yaml`

## 5. Data Ingestion and Alignment (User Story 1)

Load the raw data, align teacher/student scores with human annotations, and identify primary quality dimensions.

```bash
python code/ingest.py
```

**Inputs**:
- `data/raw/zreward_dataset.parquet` (or the file generated in Step 3)

**Outputs**:
- `data/processed/raw_data.parquet`
- Console summary of sample counts and missing data flags

## 6. Feature Engineering (User Story 2)

Calculate statistical descriptors (variance, entropy, skewness, kurtosis) and the dominant eigenvalue for entanglement quantification.

```bash
python code/features.py
```

**Inputs**:
- `data/processed/raw_data.parquet`

**Outputs**:
- `data/processed/features.json` (or `data/processed/cleaned_data.parquet` depending on integration)
- Includes per-sample stats and global dominant eigenvalue.

*Note: Task T024 (Fidelity Loss Calculation) is often integrated here or run as a separate step before model training.*

```bash
python code/fidelity_loss.py
```

**Output**:
- `data/processed/cleaned_data.parquet` (filtered dataset with `fidelity_loss` column)

## 7. Model Training and Evaluation (User Story 3)

Train a Random Forest regressor, perform cross-validation, permutation tests, and null baseline comparisons.

```bash
python code/train.py
```

**Inputs**:
- `data/processed/cleaned_data.parquet`

**Outputs**:
- `results/model.pkl` (serialized Random Forest model)
- `data/processed/split_config.json` (stratification configuration)

```bash
python code/evaluate.py
```

**Inputs**:
- `results/model.pkl`
- `data/processed/cleaned_data.parquet`

**Outputs**:
- `results/results.json` (containing R², MAE, p-values, and baseline comparisons)

## 8. Integration and Final Results (Task T031)

Run the integrated pipeline to ensure all steps execute correctly end-to-end and generate the final results file.

```bash
python code/integrate_train_eval.py
```

**Output**:
- `results/results.json` (Final aggregated metrics)

## 9. Validation and Testing

### Run Unit Tests
Execute the test suite to verify individual components:
```bash
pytest tests/ -v
```

### Validate Quickstart
Run the validation script to ensure all directories and files are present and correct:
```bash
python code/validate_quickstart.py
```

## Troubleshooting

- **Missing Dependencies**: Ensure you are in the correct project directory and `requirements.txt` was installed with the `-r` flag.
- **Data Download Failures**: If `download_zreward.py` fails, check your internet connection or try running it with `--verbose` to see specific error messages. The script has a synthetic fallback.
- **Memory Errors**: If processing fails due to memory constraints, ensure you are using a machine with sufficient RAM or reduce the dataset size by adjusting the sampling logic in `code/ingest.py`.
- **Schema Mismatches**: If `schema_discovery.py` fails, verify that the downloaded dataset matches the expected columns defined in `specs/001-llmxive-entanglement-analysis/contracts/dataset.schema.yaml`.

## Reproducibility Checklist

- [ ] All dependencies installed from `code/requirements.txt`
- [ ] Dataset downloaded to `data/raw/`
- [ ] Raw data ingested to `data/processed/raw_data.parquet`
- [ ] Features calculated and saved to `data/processed/features.json`
- [ ] Model trained and saved to `results/model.pkl`
- [ ] Final results written to `results/results.json`
- [ ] All tests pass (`pytest tests/`)

For further details, refer to the specific task documentation in the `docs/` directory or the source code comments.