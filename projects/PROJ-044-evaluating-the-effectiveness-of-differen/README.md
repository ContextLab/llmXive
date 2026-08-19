# Evaluating the Effectiveness of Differential Privacy in Federated Learning

This project investigates how Differential Privacy (DP) affects model utility and fairness in Federated Learning (FL) under varying degrees of data heterogeneity.

## ⚠️ Important: Dataset Scope

**FEMNIST Only**: This project exclusively uses the FEMNIST dataset from the LEAF benchmark (hosted on Hugging Face).
**Shakespeare Excluded**: The Shakespeare dataset has been explicitly excluded from this study due to the lack of a verified, programmatic source as identified in the project's Gap Analysis (plan.md). Any attempt to run experiments with "shakespeare" will raise a `ValueError`.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-044-evaluating-the-effectiveness-of-differen
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 *Required dependencies include:*
 - `torch`
 - `opacus`
 - `datasets` (Hugging Face)
 - `pandas`, `numpy`, `scipy`
 - `matplotlib`, `statsmodels`

4. **Install pre-commit hooks**:
 ```bash
 pre-commit install
 ```

## Usage

### 1. Data Preparation (User Story 1)

Download FEMNIST and generate Dirichlet partitions.

```bash
# Download FEMNIST (creates data/raw/femnist.parquet and.sha256)
python code/data/download.py --dataset femnist

# Generate partitions with specific alpha and seed
python code/data/partition.py --dataset femnist --seed 42 --alpha 0.1
```

**CLI Arguments**:
- `--dataset`: Dataset name (only `femnist` is supported).
- `--seed`: Random seed for reproducibility.
- `--alpha`: Dirichlet concentration parameter (e.g., 0.1, 0.5, 1.0).
- `--output`: Output directory for partition metadata (default: `data/partitions/`).

### 2. Training (User Story 2)

Run the Federated Learning experiment with Differential Privacy.

```bash
python code/training/orchestrate_experiment.py \
 --dataset femnist \
 --seeds 42 43 44 45 46 \
 --alphas 0.1 0.5 1.0 \
 --epsilons 0.1 0.5 1.0 5.0 10.0 \
 --output results/raw_logs.csv
```

**CLI Arguments**:
- `--dataset`: Dataset name (`femnist`).
- `--seeds`: List of random seeds for the 5-seed orchestration loop.
- `--alphas`: List of heterogeneity levels.
- `--epsilons`: List of privacy budgets (ε).
- `--output`: Path to the output CSV log file.

**Output**:
- `results/raw_logs.csv`: Contains per-round metrics including global accuracy, majority/minority accuracy, privacy budget spent, and flags for time limits or utility collapse.

### 3. Analysis (User Story 3)

Perform statistical analysis and generate plots.

```bash
python code/analysis/stats.py \
 --input results/raw_logs.csv \
 --output results/summary.csv \
 --plots-dir results/plots/
```

**CLI Arguments**:
- `--input`: Path to the raw training logs CSV.
- `--output`: Path for the summary statistics CSV.
- `--plots-dir`: Directory for generated plots (PNG, 300 DPI).

**Outputs**:
- `results/filtered_data.csv`: Data with time-limited and utility-collapsed runs removed.
- `results/summary.csv`: Aggregated metrics and p-values.
- `results/plots/`:
 - `accuracy_gap_vs_alpha.png`
 - `accuracy_vs_epsilon.png`
 - `minority_degradation_overlay.png`
- `results/validation_report.md`: Report on excluded runs and statistical power.

## Results

The analysis produces the following key artifacts in the `results/` directory:

1. **`summary.csv`**: A comprehensive table containing:
 - `seed`, `alpha`, `epsilon`
 - `global_accuracy`, `majority_accuracy`, `minority_accuracy`
 - `rounds_to_target`
 - `p_value_dp_vs_nondp` (per seed)
 - `p_value_majority_vs_minority`

2. **`validation_report.md`**: Details on:
 - Count of runs excluded due to `is_time_limited` or `is_utility_collapse`.
 - Flags for reduced statistical power (Mann-Whitney U fallback).

3. **Plots**:
 - **Accuracy Gap vs. Alpha**: Shows how heterogeneity impacts the DP vs. Non-DP gap.
 - **Accuracy vs. Epsilon**: Convergence curves across privacy budgets.
 - **Minority Degradation Overlay**: Explicitly compares minority client accuracy against global accuracy to assess fairness impact.

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical tests and plotting
│ ├── data/ # Downloaders and partitioning logic
│ ├── models/ # Model definitions (SmallCNN)
│ ├── training/ # FedAvg orchestrator, DP utils, logging
│ ├── config.py # Configuration management
│ └── setup_project_structure.py
├── data/
│ ├── raw/ # Downloaded datasets (femnist.parquet)
│ └── partitions/ # Dirichlet partition metadata
├── results/
│ ├── raw_logs.csv
│ ├── filtered_data.csv
│ ├── summary.csv
│ ├── validation_report.md
│ └── plots/ # Generated PNG figures
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt
├── README.md
└── tree_output.txt
```

## Contributing

Please read the `CONTRIBUTING.md` (if available) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License.
