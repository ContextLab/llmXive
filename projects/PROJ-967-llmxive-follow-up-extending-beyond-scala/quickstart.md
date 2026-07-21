# Quickstart Guide: llmXive Follow-up (Teacher Entanglement vs. Scalar Distillation Loss)

This guide provides step-by-step instructions to reproduce the full research pipeline
from raw data acquisition to final model evaluation, satisfying Constitution Principle I (Reproducibility).

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- At least 8GB RAM (for full dataset processing) or 4GB for sampled processing
- Internet connection (for initial dataset download)

## 1. Project Setup

Navigate to the project directory:
```bash
cd projects/PROJ-967-llmxive-follow-up-extending-beyond-scala
```

Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r code/requirements.txt
```

## 2. Data Acquisition

Download the Z-Reward dataset and validate its integrity.
This step fetches real data from the official source and computes a SHA256 checksum.

```bash
python code/ingest.py --action download
```

**Expected Output:**
- Dataset saved to `data/raw/zreward_dataset.csv`
- Checksum file created at `data/.checksums`
- Console log: "Dataset downloaded and verified successfully."

**Note:** If the download fails, the system will automatically attempt to generate synthetic fallback data (T039), but this is only for development purposes. For production runs, ensure the real dataset is available.

## 3. Data Validation

Validate the dataset schema against the defined contracts.
This ensures all required columns (prompt, image_path, teacher_logits, student_scalar, human_annotations, primary_dimension) are present.

```bash
python code/ingest.py --action validate
```

**Expected Output:**
- Schema validation report printed to console
- Missing data flags for any incomplete samples
- Summary of dimension coverage

## 4. Feature Engineering

Compute entanglement features, global eigenvalues, and dimensional fidelity loss.
This step processes the aligned data and generates the feature set required for modeling.

```bash
python code/features.py
```

**Expected Output:**
- Feature set saved to `data/processed/features.json`
- Console log with statistics: sample counts, variance ranges, global eigenvalue, fidelity loss metrics
- Verification that output matches `contracts/output.schema.yaml`

## 5. Model Training

Train a Random Forest regressor to predict fidelity loss using entanglement features.
The model uses CPU-only execution with 5-fold cross-validation.

```bash
python code/train.py
```

**Expected Output:**
- Model artifact saved to `results/model.pkl`
- Cross-validation metrics printed to console (R², MAE)
- Memory usage logs (if profiling enabled)

## 6. Model Evaluation

Evaluate the trained model using permutation tests to verify statistical significance.
This step compares the model's performance against a null baseline.

```bash
python code/evaluate.py
```

**Expected Output:**
- Results saved to `results/results.json`
- Metrics: R², MAE, Permutation test p-value
- Console log: "Evaluation complete. Results saved to results/results.json"

## 7. Full Pipeline Execution (Optional)

To run the entire pipeline from data ingestion to evaluation in one command:

```bash
python code/integrate_pipeline.py
python code/integrate_train_eval.py
```

**Expected Output:**
- All intermediate artifacts generated in their respective directories
- Final results in `results/results.json`

## 8. Validation

Verify that the pipeline execution was successful and all artifacts are in place.

```bash
python code/validate_quickstart.py
```

**Expected Output:**
- Directory structure validation
- File existence checks for all required artifacts
- Pipeline execution validation
- Results content verification
- Final status: "All validations passed."

## Troubleshooting

### Memory Issues
If you encounter memory errors during feature engineering or model training:
- Reduce the dataset size by sampling (modify `code/ingest.py` to use `streaming=True` and limit rows)
- Ensure you have at least 8GB of free RAM

### Dataset Download Fails
- Check your internet connection
- Verify the Z-Reward dataset URL is accessible
- If the official source is down, the system will fall back to synthetic data (T039)

### Schema Validation Errors
- Ensure `contracts/dataset.schema.yaml` matches the expected structure
- Check that all required columns are present in the dataset

### Model Training Errors
- Verify that `data/processed/features.json` contains valid data
- Ensure the Random Forest model parameters are correctly configured in `code/train.py`

## Reproducibility Notes

- All dependencies are pinned in `code/requirements.txt`
- Random seeds are set to 42 for all stochastic processes
- Dataset checksums are stored in `data/.checksums`
- All scripts log their execution details to `logs/` directory
- The full pipeline can be reproduced by running the commands in sections 2-6 in order

## Contact & Support

For issues or questions, refer to the project's `README.md` or contact the maintainers.