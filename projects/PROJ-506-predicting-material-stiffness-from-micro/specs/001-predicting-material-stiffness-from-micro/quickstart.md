# Quickstart: Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks

## Prerequisites

- Python 3.10+
- pip / virtualenv
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-506-predicting-material-stiffness-from-micro
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Generation

Run the synthetic data generation script:

```bash
python code/data_generation/generate_microstructures.py --num_samples 2000 --output_dir data/raw
```

This will:
- Generate ≥ 2,000 256x256 grayscale images.
- Compute stiffness tensors via FFT-based homogenization.
- Save metadata to `data/raw/metadata.csv`.

## Training

Train the CNN model:

```bash
python code/training/train.py --data_dir data/raw --epochs 50 --batch_size 32 --cv_folds 5
```

This will:
- Perform 5-fold cross-validation.
- Train a shallow CNN on CPU.
- Save model weights to `code/models/`.

## Evaluation

Evaluate the model and generate reports:

```bash
python code/evaluation/evaluate.py --model_path code/models/best_model.pth --test_dir data/raw
```

This will:
- Compute MAE, MSE, R-squared.
- Perform statistical tests (paired t-tests) across density bins.
- Flag outliers and out-of-distribution cases.
- Save results to `data/reports/`.

## Running Tests

Execute the test suite:

```bash
pytest tests/ -v
```

This includes:
- Unit tests for generation, homogenization, and model.
- Contract tests validating data/output schemas.
- Integration tests for the full pipeline.

## Expected Outputs

- **Images**: `data/raw/images/` (PNG files)
- **Metadata**: `data/raw/metadata.csv`
- **Models**: `code/models/*.pth`
- **Reports**: `data/reports/metrics.json`, `data/reports/statistical_analysis.csv`

## Troubleshooting

- **Memory Errors**: Reduce batch size or image resolution.
- **Runtime Exceeded**: Reduce epochs or dataset size.
- **FFT Convergence Issues**: Check for extreme void densities (>90%) and adjust solver parameters.
