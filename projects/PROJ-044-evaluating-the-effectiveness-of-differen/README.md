# Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Project ID**: PROJ-044
**Status**: Research Implementation
**Dataset**: FEMNIST (Federated Extended MNIST)

## Overview

This project investigates the impact of Differential Privacy (DP) on Federated Learning (FL) performance, specifically focusing on the "Critical Heterogeneity" hypothesis: that DP disproportionately degrades performance for minority clients in highly non-IID data distributions.

**⚠️ Important Dataset Restriction**:
Per the project specification (T000) and `plan.md` Gap Analysis, the **Shakespeare dataset is explicitly excluded** from this project due to the lack of a verified, programmatically accessible source. All experiments and analyses are conducted exclusively on the **FEMNIST** dataset.

## Installation

### Prerequisites
- Python 3.10+
- pip
- git

### Setup

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-044-evaluating-the-effectiveness-of-differen
 ```

2. **Create and activate a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

4. **Initialize project structure and pre-commit hooks**:
 ```bash
 python code/setup_project_structure.py
 pre-commit install
 ```

## Usage

The pipeline is executed in three sequential phases: Data Preparation, Training, and Analysis.

### Phase 1: Data Preparation

Download and partition the FEMNIST dataset.

```bash
# Download FEMNIST (Verified Source: leaf/femnist)
python code/data/download.py --dataset femnist

# Generate Dirichlet partitions for specific configurations
# Example: Alpha=0.1, Seed=42
python code/data/generate_partition_metadata.py --alpha 0.1 --seed 42 --dataset femnist
```

**Expected Outputs**:
- `data/raw/femnist.parquet`: Raw dataset
- `data/raw/femnist.sha256`: Checksum verification
- `data/partitions/partition_femnist_{seed}_{alpha}.json`: Client partition metadata

### Phase 2: Training (DP-FedAvg)

Run the federated learning experiments with varying privacy budgets ($\epsilon$) and heterogeneity levels ($\alpha$).

```bash
# Run the full experiment orchestration (5 seeds per configuration)
python code/training/run_experiment_orchestrator.py \
 --dataset femnist \
 --alphas 0.1 0.5 1.0 \
 --epsilons 0.5 1.0 5.0 \
 --seeds 42 123 456 789 999
```

**Key Arguments**:
- `--dataset`: Must be `femnist` (Shakespeare is excluded).
- `--alphas`: Dirichlet concentration parameters (e.g., `0.1` for high heterogeneity).
- `--epsilons`: Privacy budgets ($\epsilon$). Lower values mean stricter privacy.
- `--seeds`: Random seeds for reproducibility (5 seeds required per config).

**Expected Outputs**:
- `results/raw_logs.csv`: Per-round metrics for all seeds.
- `results/filtered_time.csv`: Logs excluding time-limited runs.
- `results/filtered_data.csv`: Logs excluding utility collapse and time-limited runs.

### Phase 3: Statistical Analysis

Perform statistical testing and generate visualizations.

```bash
# Run the full analysis pipeline
python code/analysis/stats.py
```

**Expected Outputs**:
- `results/summary.csv`: Aggregated metrics including p-values and variance.
- `results/plots/minority_vs_global_overlay.png`: Overlay plot of minority vs global accuracy degradation.
- `results/slope_ratio_validation.md`: Validation report for SC-004.
- `results/validation_report.md`: Summary of excluded runs and statistical power flags.

## Results

The analysis produces the following key artifacts:

1. **`results/summary.csv`**: Contains the final aggregated results per configuration.
 - Columns include `global_accuracy`, `minority_accuracy`, `p_value_dp_vs_nondp`, and `accuracy_variance`.
 - `p_value_dp_vs_nondp` is a JSON-encoded string of individual p-values per seed.

2. **`results/plots/minority_vs_global_overlay.png`**: Visualizes the accuracy gap between global and minority clients across $\epsilon$ values.

3. **`results/slope_ratio_validation.md`**: Confirms whether the accuracy degradation slope for $\alpha=0.1$ is at least 2x steeper than for $\alpha=1.0$.

## Validation

To verify the project setup and data integrity:

```bash
python code/validation/validate_quickstart.py
```

This script checks:
- Directory structure
- `tree_output.txt` existence
- Requirements installation
- Data checksums
- Partition metadata format
- Training logs
- Filtered data availability
- Plot DPI validation (300 DPI)

## Architecture

- **`code/data/`**: Downloading, partitioning, and checksumming utilities.
- **`code/training/`**: FedAvg orchestrator, DP noise wrappers, and experiment logging.
- **`code/analysis/`**: Statistical tests (t-tests, Mann-Whitney U), plotting, and aggregation.
- **`code/models/`**: Model definitions (SmallCNN for FEMNIST).
- **`data/raw/`**: Raw dataset files (FEMNIST only).
- **`data/partitions/`**: Client partition metadata JSON files.
- **`results/`**: Training logs, filtered data, plots, and final reports.

## Contributing

Please adhere to the project's linting and formatting standards (Black, Ruff) before submitting changes.

```bash
pre-commit run --all-files
```

## License

[Insert License Information]
