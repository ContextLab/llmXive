# llmXive: Agentic Abstention Research Pipeline

## Overview
llmXive is an automated science pipeline designed to investigate whether AI agents know when to stop acting and instead abstain. This project implements a Meta-Critic model that predicts optimal abstention points based on low-level state features, aiming to reduce token consumption by at least 40% compared to full-context baselines. [UNRESOLVED-CLAIM: c_e7a75df3 — status=refuted]

## Project Structure

```
.
├── code/ # Core implementation
│ ├── analysis/ # Statistical analysis and reporting
│ ├── data/ # Data ingestion, feature extraction, preprocessing
│ ├── models/ # Meta-Critic model training and evaluation
│ ├── oracle/ # Ground truth solver for abstention labels
│ ├── simulation/ # Agent interaction simulation framework
│ ├── config.py # Configuration management
│ └── logging_config.py # Logging setup
├── data/ # Data storage
│ ├── raw/ # Raw benchmark data
│ ├── processed/ # Processed features and labels
│ └── results/ # Simulation results and reports
├── tests/ # Test suite
│ ├── contract/ # Schema and output contract tests
│ └── integration/ # Integration tests for pipelines
├── docs/ # Documentation
├── specs/ # Feature specifications and design docs
├── requirements.txt # Python dependencies
└── quickstart.md # Quick start guide
```

## Prerequisites

- Python 3.11+
- pip package manager
- Access to Hugging Face Hub (for benchmark data)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmXive
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

## Quick Start

For a complete guide on running the pipeline, see [`quickstart.md`](../quickstart.md).

The pipeline consists of three main phases:

1. **Data Ingestion & Feature Extraction** (User Story 1)
 - Fetches the "Agentic Abstention" benchmark dataset
 - Extracts low-level state features (search count, error frequency, token usage, etc.)
 - Generates ground truth abstention labels using an oracle solver

2. **Meta-Critic Model Training** (User Story 2)
 - Trains an XGBoost classifier to predict abstention points
 - Runs simulations comparing Meta-Critic vs. full-context baseline
 - Evaluates token reduction and latency metrics

3. **Statistical Validation** (User Story 3)
 - Performs statistical significance testing (Mann-Whitney U, Kolmogorov-Smirnov)
 - Conducts survival analysis on token consumption
 - Generates sensitivity analysis across decision thresholds

## Key Components

### Data Pipeline
- `code/data/ingest.py`: Fetches and verifies real benchmark data
- `code/data/extract_features.py`: Computes state features from interaction trajectories
- `code/data/preprocess.py`: Handles missing values and validates dataset quality

### Model Training
- `code/models/train_meta_critic.py`: Trains the Meta-Critic classifier
- `code/simulation/simulation_framework.py`: Runs agent interaction loops
- `code/oracle/solver.py`: Generates ground truth abstention labels

### Analysis
- `code/analysis/statistical_tests.py`: Performs significance testing
- `code/analysis/survival_analysis.py`: Analyzes censored token consumption data
- `code/analysis/sensitivity_analysis.py`: Sweeps decision thresholds

## Configuration

Configuration is managed via `config.yaml` or environment variables. Key settings include:
- Data paths
- Random seeds for reproducibility
- Hyperparameters for model training
- Simulation parameters (max turns, token budgets)

See `code/config.py` for available configuration options.

## Testing

Run the full test suite:
```bash
pytest tests/
```

Run specific test categories:
```bash
pytest tests/contract/ # Schema validation tests
pytest tests/integration/ # Integration tests
```

## Results

After running the pipeline, results are stored in `data/results/`:
- `baseline_comparison.json`: Metrics comparing Meta-Critic vs. baseline
- `statistical_report.md`: Detailed statistical analysis report
- Sensitivity analysis plots and data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Ensure all tests pass
5. Submit a pull request

## License

[License information to be added]

## Citation

If you use this code in your research, please cite:
```bibtex
@misc{llmxive2024,
 title={llmXive: Agentic Abstention Research Pipeline},
 year={2024},
 url={
}
```
