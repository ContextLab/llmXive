# Quickstart: Molecular Charge Prediction

## Prerequisites
- Python 3.11+
- Access to a GitHub Actions free-tier runner (or local environment with 7 GB+ RAM).
- Internet access to download QM9 from Hugging Face.

## Installation
1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r projects/PROJ-404-predicting-molecular-surface-charge-dist/code/requirements.txt
    ```

## Data Preparation
The data is loaded directly from the Hugging Face dataset. No manual download is required.
The `loader.py` script handles streaming and filtering.
```bash
# Verify data loading and schema
python projects/PROJ-404-predicting-molecular-surface-charge-dist/code/data/loader.py --verify
```

## Training
Run the training script. This will:
1.  Load the QM9 subset.
2.  Perform a scaffold-based split.
3.  Train the 3D GNN (SchNet/DimeNet).
4.  Train the 2D baseline.
5.  Save model weights and logs.

```bash
python projects/PROJ-404-predicting-molecular-surface-charge-dist/code/train/trainer.py --epochs 10 --seed 42
```

## Evaluation
Run the evaluation script to generate the final report and validate the hypothesis.
```bash
python projects/PROJ-404-predicting-molecular-surface-charge-dist/code/eval/evaluator.py
```
This script will output a JSON report and set an exit code based on the hypothesis validation (MAE ≤ 0.05 e and improvement over baseline).

## Testing
Run the unit and integration tests to ensure the pipeline is working correctly.
```bash
pytest projects/PROJ-404-predicting-molecular-surface-charge-dist/tests/
```
