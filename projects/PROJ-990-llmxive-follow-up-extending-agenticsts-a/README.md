# llmXive: AgenticSTS Follow-up Project

## Project Overview

This project implements an automated science pipeline for extending the "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents" research. The system analyzes LLM agent trajectories, performs ablation studies to determine memory layer utility, trains a lightweight classifier to predict optimal retrieval strategies, and validates a dynamic policy against static baselines.

## Key Features

- **Dynamic Retrieval Policy**: Uses a trained classifier to select memory layers based on turn-level entropy and token budget constraints.
- **Ablation Study Engine**: Computes ground-truth utility scores for memory layers via systematic ablation.
- **Baseline Comparisons**: Implements "Static All-Layers" and "No-Store Random" baselines for rigorous comparison.
- **Statistical Validation**: Performs McNemar's tests (paired) or Permutation tests (unpaired) with Bonferroni correction to validate efficacy.
- **Bounded-Memory Simulation**: Enforces hard token budgets (4096) and minimum context floors (256) during simulation.

## Quick Start

See [`quickstart.md`](quickstart.md) for step-by-step instructions on running the full pipeline, including data validation, training, simulation, and statistical reporting.

## Project Structure

```
.
├── code/ # Core implementation modules
│ ├── config.py # Configuration constants (TOKEN_BUDGET, MIN_CONTEXT)
│ ├── parser.py # Trajectory parsing and metric extraction
│ ├── entropy.py # Shannon entropy calculation for move distributions
│ ├── splitter.py # Stratified data splitting
│ ├── ablation.py # Ablation study engine
│ ├── classifier.py # Utility prediction model training and validation
│ ├── simulator.py # Dynamic and baseline simulation logic
│ ├── stats.py # Statistical testing (McNemar, Permutation, t-test)
│ └── main.py # Pipeline orchestration
├── data/
│ ├── raw/ # Input trajectory logs (checksum-verified)
│ └── processed/ # Derived metrics, splits, and analysis outputs
├── models/ # Trained classifier artifacts
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── quickstart.md # Execution guide
```

## Dependencies

- Python 3.11+
- pandas, numpy, scikit-learn, pytest, pyyaml
- (Optional) ruff, black for linting/formatting

Install dependencies:
```bash
pip install -r requirements.txt
```

## Execution Workflow

1. **Data Validation**: Ensure `data/raw/` contains valid, checksum-verified trajectory files.
2. **Parsing**: Extract per-turn metrics and move distributions (`code/parser.py`).
3. **Entropy Calculation**: Compute Shannon entropy of legal move distributions (`code/entropy.py`).
4. **Data Splitting**: Stratified split into training and hold-out sets (`code/splitter.py`).
5. **Ablation Study**: Run ablation on both sets to generate utility labels (`code/ablation.py`).
6. **Validation**: Verify proxy correlation and sample size sufficiency (`code/classifier.py`, `code/validator.py`).
7. **Training**: Train the layer utility classifier (`code/classifier.py`).
8. **Simulation**: Run Dynamic, Static, and Random agents (`code/simulator.py`).
9. **Aggregation**: Compute win rates and token usage statistics (`code/stats.py`).
10. **Statistical Testing**: Perform significance tests with Bonferroni correction (`code/stats.py`).
11. **Reporting**: Generate final statistical and baseline comparison reports.

## Configuration

Key parameters are defined in `code/config.py`:
- `TOKEN_BUDGET`: Maximum token limit per prompt (default: 4096)
- `MIN_CONTEXT`: Minimum context floor (default: 256)
- Random seeds for reproducibility

## Output Artifacts

The pipeline produces the following key artifacts in `data/processed/`:
- `metrics_with_moves.csv`: Parsed trajectory metrics with move distributions.
- `train_set.csv`, `holdout_set.csv`: Stratified dataset splits.
- `ablation_labels_train.json`, `ablation_labels_holdout.json`: Utility scores from ablation.
- `proxy_validation_report.json`: Correlation analysis between static proxy and ablation utility.
- `baseline_comparison.csv`: Aggregated win rates and token usage.
- `statistical_results.json`: Final significance test results with effect sizes.
- `divergence_report.json`: Trajectory divergence detection results.

## Contributing

This project follows a strict task-based implementation workflow. See `tasks.md` for the current task list and execution order.

## License

(Insert license information here)
