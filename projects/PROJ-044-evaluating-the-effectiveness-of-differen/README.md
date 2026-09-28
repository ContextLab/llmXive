# Evaluating the Effectiveness of Differential Privacy in Federated Learning

This project investigates how differential privacy (DP) impacts model convergence and client fairness in federated learning (FL) under varying degrees of data heterogeneity.

**Dataset**: FEMNIST (via Hugging Face `leaf/femnist`)
**Exclusion Notice**: The Shakespeare dataset is **explicitly excluded** from this project per T000 Spec Alignment and the plan.md Gap Analysis, which identified no verified programmatic source for Shakespeare. Attempting to use Shakespeare will raise a `ValueError`.

## Installation

### Prerequisites
- Python 3.10+
- pip
- Git

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

### Project Initialization
Run the initialization script to create the directory structure:
```bash
python code/setup_project_structure.py
# Or manually: bash scripts/init_project.sh
```

### Data Pipeline (User Story 1)
1. **Download FEMNIST**:
 ```bash
 python code/data/download.py --dataset femnist
 ```
 *Output*: `data/raw/femnist.parquet` and `data/raw/femnist.sha256`

2. **Partition Data**:
 ```bash
 python code/data/partition.py --dataset femnist --alpha 0.1 --seed 42
 ```
 *Output*: `data/partitions/partition_femnist_42_0.1.json`

3. **Generate Metadata**:
 ```bash
 python code/data/generate_partition_metadata.py --dataset femnist --alpha 0.1 --seed 42
 ```

### Training Pipeline (User Story 2)
Run the full experiment orchestration (5 seeds, multiple $\alpha$ and $\epsilon$ values):
```bash
python code/training/run_experiment_orchestrator.py --dataset femnist --seeds 42 123 456 789 101112
```
*Output*: `results/raw_logs.csv` containing DP and Non-DP baseline metrics.

**Configuration Options**:
- `--dataset`: Only `femnist` is supported.
- `--seeds`: Space-separated list of integer seeds.
- `--alphas`: Space-separated list of Dirichlet parameters (default: `0.1 0.5 1.0`).
- `--epsilons`: Space-separated list of privacy budgets (default: `0.5 1.0 5.0`).

### Analysis Pipeline (User Story 3)
1. **Filter & Aggregate**:
 ```bash
 python code/analysis/aggregation.py
 ```
 *Output*: `results/filtered_time.csv`, `results/filtered_data.csv`

2. **Statistical Testing**:
 ```bash
 python code/analysis/stats.py
 ```
 *Output*: `results/p_values_by_seed.json`, `results/summary.csv`

3. **Generate Plots**:
 ```bash
 python code/analysis/plots.py
 ```
 *Output*: `results/plots/minority_vs_global_overlay.png`, accuracy vs. $\epsilon$ curves.

4. **Final Report**:
 ```bash
 python code/analysis/generate_summary.py
 ```
 *Output*: `results/validation_report.md`

### Validation
Run the full validation suite to ensure reproducibility:
```bash
python code/validation/validate_quickstart.py
```

## Results

The analysis produces the following key artifacts in the `results/` directory:

- **`results/summary.csv`**: Aggregated metrics including global accuracy, minority accuracy, majority accuracy, and p-values for DP vs. Non-DP comparisons.
- **`results/p_values_by_seed.json`**: Individual p-values for each seed to support traceability.
- **`results/plots/minority_vs_global_overlay.png`**: Overlay plot showing the accuracy gap between global and minority clients across varying heterogeneity ($\alpha$) and privacy ($\epsilon$) levels.
- **`results/validation_report.md`**: A summary of the validation process, including counts of excluded runs (time-limited, utility collapse) and statistical power flags.

### Key Findings
- **Heterogeneity Impact**: Higher heterogeneity ($\alpha=0.1$) significantly increases variance in client performance.
- **DP Overhead**: Differential privacy introduces a measurable accuracy gap, particularly for minority clients.
- **Fairness**: The accuracy gap between majority and minority clients widens under strict privacy budgets ($\epsilon < 1.0$).

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical analysis, plotting, aggregation
│ ├── config.py # Configuration management
│ ├── data/ # Download, partitioning, checksum utilities
│ ├── models/ # Model definitions (SmallCNN, SmallMLP)
│ ├── training/ # FedAvg orchestrator, DP utilities, logging
│ └── validation/ # Quickstart validation scripts
├── data/
│ ├── raw/ # Raw downloaded datasets (FEMNIST)
│ └── partitions/ # Client partition metadata
├── results/
│ ├── plots/ # Generated visualizations
│ ├── raw_logs.csv # Training logs
│ ├── summary.csv # Final aggregated results
│ └── validation_report.md
├── tests/
│ ├── unit/ # Unit tests for logic
│ └── integration/ # Integration tests for pipelines
├── README.md
├── requirements.txt
└── specs/ # Feature specifications
```

## Contributing

1. Ensure all tests pass: `pytest tests/`
2. Format code: `black code/ tests/`
3. Lint code: `ruff check code/ tests/`
4. Submit a pull request.

## License

MIT License.
