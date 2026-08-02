# Architecture Documentation

## Overview

This document describes the architectural design of the Differential Privacy in Federated Learning evaluation pipeline. The system is designed to be modular, reproducible, and extensible, allowing for independent implementation and testing of research components.

## Core Components

### 1. Data Layer (`code/data/`)

Responsible for data acquisition, validation, and partitioning.

- **`download.py`**: Handles downloading of raw datasets (FEMNIST, Shakespeare) from Hugging Face Hub. Implements retry logic and checksum verification.
- **`partition.py`**: Implements Dirichlet distribution-based partitioning to simulate non-IID data across clients. Supports configurable α parameters to control heterogeneity.
- **`checksum_utils.py`**: Provides SHA256 checksum generation and verification for data integrity.

**Data Flow**:
1. Raw data is downloaded from Hugging Face Hub.
2. Checksums are generated and stored for verification.
3. Data is partitioned into client-specific subsets based on Dirichlet sampling.
4. Partition metadata is saved as JSON files.

### 2. Model Layer (`code/models/`)

Defines the neural network architectures used in the experiments.

- **`cnn.py`**: Contains `SmallCNN` and `SmallMLP` implementations optimized for FEMNIST and Shakespeare datasets.

**Design Decisions**:
- Models are kept lightweight to facilitate rapid experimentation on CPU/GPU.
- Architecture is abstracted to allow easy swapping of model types.

### 3. Training Layer (`code/training/`)

Implements the Federated Learning training loop with Differential Privacy.

- **`fedavg.py`**: Orchestrates the FedAvg algorithm, managing client selection, model aggregation, and privacy budget tracking.
- **`dp_utils.py`**: Configures Opacus for DP-SGD, including noise multiplier calculation and moments accountant setup.
- **`logging.py`**: Handles structured logging of training metrics (accuracy, loss, privacy budget) to CSV and JSON formats.

**Key Features**:
- Support for multiple privacy budgets (ε).
- Detection of "utility collapse" for extremely low ε values.
- Timeout handling and early stopping.
- Separate logging for majority and minority clients.

### 4. Analysis Layer (`code/analysis/`)

Performs statistical analysis and visualization of experimental results.

- **`stats.py`**: Implements statistical tests (t-tests, Mann-Whitney U), calculates summary statistics, and generates validation reports.
- **`plots.py`**: Generates visualizations including accuracy gap vs. α, accuracy vs. ε, and minority degradation overlays.

**Analysis Workflow**:
1. Load training metrics from CSV.
2. Filter out time-limited runs.
3. Calculate summary statistics and perform statistical tests.
4. Generate plots and validation reports.

### 5. Configuration (`code/config.py`)

Centralized configuration management using a `Config` dataclass.

**Supported Parameters**:
- `seed`: Random seed for reproducibility.
- `alpha`: Dirichlet parameter for heterogeneity.
- `epsilon`: Privacy budget.
- `dataset`: Dataset name (`femnist` or `shakespeare`).

## Data Models

### Partition Metadata

Stored in `data/partitions/` as JSON files.

```json
{
 "client_id": "client_0",
 "label_distribution": {
 "0": 0.1,
 "1": 0.2,
...
 },
 "total_samples": 100
}
```

### Training Metrics

Stored in `results/` as CSV files.

| Column | Description |
|--------|-------------|
| seed | Random seed |
| alpha | Heterogeneity parameter |
| epsilon | Privacy budget |
| round | Training round number |
| global_accuracy | Global model accuracy |
| minority_accuracy | Accuracy on minority clients |
| majority_accuracy | Accuracy on majority clients |
| is_time_limited | Flag for timeout |

## Dependencies

- **PyTorch**: Core deep learning framework.
- **Opacus**: Differential privacy library for PyTorch.
- **Hugging Face Datasets**: Data loading and preprocessing.
- **Pandas/NumPy**: Data manipulation and analysis.
- **SciPy**: Statistical tests.
- **Matplotlib**: Visualization.

## Security & Privacy

- All data downloads are verified via SHA256 checksums.
- Differential privacy is enforced via Opacus with strict privacy budget tracking.
- No synthetic data fallbacks are permitted; failures are explicit.

## Extensibility

The modular design allows for easy addition of:
- New datasets (by extending `download.py`).
- New partitioning strategies (by extending `partition.py`).
- New statistical tests (by extending `stats.py`).
- New model architectures (by extending `models/`).
