# Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Overview

This project investigates the impact of Differential Privacy (DP) on Federated Learning (FL) convergence and fairness, specifically focusing on the "critical heterogeneity" hypothesis. We simulate client data partitions using Dirichlet distributions with varying concentration parameters (α) and train models using FedAvg with Opacus-enabled DP.

**Important Note on Datasets**: This project currently supports **FEMNIST** only. The Shakespeare dataset is explicitly excluded per the project plan due to lack of verified programmatically-accessible sources. Attempting to run with Shakespeare will raise a `ValueError`.

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-044-evaluating-the-effectiveness-of-differen
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. (Optional) Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

### Configuration

The project uses a `Config` dataclass defined in `code/config.py`. Key parameters include:
- `seed`: Random seed for reproducibility.
- `alpha`: Dirichlet concentration parameter (controls heterogeneity).
- `epsilon`: Privacy budget (DP strength).
- `dataset`: Currently only `"femnist"` is supported.

### Data Preparation

Download and partition the FEMNIST dataset:

```bash
# Download FEMNIST data
python code/data/download.py --dataset femnist

# Partition data with specific alpha and seed
python code/data/partition.py --alpha 0.1 --seed 42 --dataset femnist
```

Outputs:
- `data/raw/femnist.parquet`: Raw dataset in Parquet format.
- `data/raw/femnist.sha256`: Checksum file for verification.
- `data/partitions/`: Directory containing partition metadata JSON files.

### Training

Run the DP-FL training experiment:

```bash
python code/training/orchestrate_experiment.py \
 --alpha 0.1 \
 --epsilon 0.5 \
 --seeds 42 123 456 789 101 \
 --dataset femnist
```

Outputs:
- `results/raw_logs.csv`: Detailed training metrics per round.

### Analysis

Perform statistical analysis and generate plots:

```bash
python code/analysis/stats.py
```

This script:
1. Filters out time-limited and utility-collapse runs.
2. Calculates rounds to target accuracy.
3. Performs paired t-tests (DP vs Non-DP).
4. Performs unpaired tests (Majority vs Minority clients).
5. Generates sensitivity analysis plots.

Outputs:
- `results/filtered_data.csv`: Cleaned dataset for analysis.
- `results/plots/`: Directory containing PNG plots (300 DPI).
- `results/summary.csv`: Final results summary.
- `results/validation_report.md`: Report on excluded runs and statistical power.

### Results

The final analysis produces:
- **Accuracy Gap vs. α**: Visualizing the impact of heterogeneity.
- **Accuracy vs. ε**: Showing the trade-off between privacy and utility.
- **Minority Degradation Overlay**: Comparing minority client performance against global accuracy.
- **Statistical Significance**: P-values for DP impact and fairness gaps.

See `results/summary.csv` and `results/validation_report.md` for detailed numerical results.

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical analysis and plotting
│ ├── data/ # Data download and partitioning
│ ├── models/ # Model definitions
│ ├── training/ # Training loop and DP utilities
│ ├── config.py # Configuration management
│ └──...
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── partitions/ # Client partition metadata
├── results/
│ ├── plots/ # Generated visualization plots
│ └──... # Analysis outputs
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt
└── README.md
```

## Contributing

Please read the contribution guidelines before submitting PRs. Ensure all tests pass and code is formatted with Black and Ruff.

## License

MIT License.
