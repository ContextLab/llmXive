# Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Project ID**: PROJ-044
**Status**: Research Implementation

## Overview

This project investigates the impact of Differential Privacy (DP) on Federated Learning (FL) under varying degrees of data heterogeneity. We simulate non-IID client data distributions using Dirichlet sampling (α ∈ {0.1, 0.5, 1.0}) on the FEMNIST and Shakespeare datasets (LEAF benchmark). We train models using FedAvg with Opacus-enabled DP, tracking privacy budgets (ε) and measuring the trade-off between privacy, utility, and fairness (majority vs. minority client performance).

## Research Questions

1. How does data heterogeneity (α) affect the convergence of DP-FL compared to non-DP FL?
2. Is there a "critical heterogeneity" threshold where DP disproportionately harms minority clients?
3. What is the optimal privacy budget (ε) that balances privacy guarantees with model utility?

## Project Structure

```text
.
├── code/
│ ├── analysis/ # Statistical analysis and plotting
│ │ ├── plots.py
│ │ └── stats.py
│ ├── config.py # Configuration management
│ ├── data/ # Data download, partitioning, and utilities
│ │ ├── checksum_utils.py
│ │ ├── download.py
│ │ └── partition.py
│ ├── models/ # Model definitions (CNN, MLP)
│ │ └── cnn.py
│ ├── training/ # Training loops and DP utilities
│ │ ├── dp_utils.py
│ │ ├── fedavg.py
│ │ └── logging.py
│ └── setup_project_structure.py
├── data/
│ ├── raw/ # Downloaded raw datasets (FEMNIST, Shakespeare)
│ └── partitions/ # Client partition metadata (JSON)
├── results/ # Final analysis results and reports
│ ├── summary.csv
│ └── validation_report.md
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.10+
- CUDA-capable GPU (recommended for training)
- 16GB+ RAM (for dataset loading and partitioning)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### 1. Data Preparation

Download the FEMNIST and Shakespeare datasets from the Hugging Face Hub (LEAF benchmark).

```bash
python code/data/download.py --dataset femnist --output data/raw
python code/data/download.py --dataset shakespeare --output data/raw
```

Generate client partitions with specific heterogeneity levels:

```bash
python code/data/partition.py --dataset femnist --alpha 0.1 --seed 42
python code/data/partition.py --dataset shakespeare --alpha 0.5 --seed 42
```

### 2. Training

Run the Federated Learning experiment with Differential Privacy.

```bash
python code/training/fedavg.py \
 --dataset femnist \
 --alpha 0.1 \
 --epsilon 0.5 \
 --seed 42 \
 --output results/experiment_001
```

Key arguments:
- `--dataset`: Dataset name (`femnist` or `shakespeare`)
- `--alpha`: Dirichlet parameter for heterogeneity (0.1, 0.5, 1.0)
- `--epsilon`: Privacy budget (0.1, 0.5, 1.0, 5.0, 10.0)
- `--seed`: Random seed for reproducibility

### 3. Analysis

Perform statistical analysis on the training results.

```bash
python code/analysis/stats.py --input results/experiment_001/metrics.csv
```

Generate visualizations:

```bash
python code/analysis/plots.py --input results/experiment_001/metrics.csv --output results/figures
```

## Configuration

The `code/config.py` module provides a `Config` dataclass for managing experiment parameters:

```python
from config import Config

config = Config(
 seed=42,
 alpha=0.1,
 epsilon=0.5,
 dataset="femnist"
)
```

## Results

Final results are stored in the `results/` directory:
- `summary.csv`: Aggregated metrics (accuracy, rounds to target, p-values)
- `validation_report.md`: Statistical power analysis and experiment validation
- `figures/`: Plots showing accuracy gaps, sensitivity analysis, and minority degradation

## Testing

Run unit and integration tests:

```bash
pytest tests/unit -v
pytest tests/integration -v
```

## License

This project is part of the llmXive automated science pipeline.

## Contributing

Please refer to the project's contribution guidelines for details on adding new tasks, tests, and features.
