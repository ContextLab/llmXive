# User Guide: Solubility Prediction Pipeline

## Getting Started

This guide walks you through the process of using the pipeline to predict solubility.

### Prerequisites

- Python 3.10 or higher installed.
- pip package manager.
- Sufficient disk space for datasets and model checkpoints (~500MB).

### Step 1: Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Data Preparation

The pipeline requires the ESOL dataset. It will be downloaded automatically.

```bash
# Download and preprocess
python code/data/download_esol.py
python code/data/preprocess.py
python code/data/split.py
```

*Note: This step filters out invalid SMILES and splits the data into train/validation/test sets.*

### Step 3: Training Models

Run the baseline and GNN models sequentially or in parallel (if resources allow).

```bash
# Train Random Forest Baseline
python code/training/train_baseline.py

# Train GNN MPNN
python code/training/train_gnn.py
```

### Step 4: Analyzing Results

Once training is complete, run the evaluation scripts.

```bash
# Statistical significance test
python code/evaluation/statistical_test.py

# Generate final report
python code/evaluation/report_generator.py
```

### Step 5: Visualizing Outputs

Check the `results/` directory for:
- `final_report.txt`: Summary of metrics and statistical tests.
- `plots/`: Visualizations of feature importance and prediction distributions.

## Customization

- **Adjusting Model Hyperparameters**: Edit `code/models/gnn_mpnn.py` or `code/models/baseline_rf.py`.
- **Changing Data Split**: Modify `code/data/split.py` to adjust stratification bins.
- **Logging**: Configure log levels in `code/setup_logging.py`.

## Support

For issues or questions, please refer to the `docs/` directory or open an issue in the repository.