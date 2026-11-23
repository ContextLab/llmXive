# llmXive: Where Do Deep-Research Agents Go Wrong?

This project implements an automated pipeline to analyze the topological structure of
deep-research agent trajectories (specifically from the TELBench dataset) to identify
early-stage patterns that predict eventual collapse.

## Overview

The pipeline parses agent trajectories, constructs a Directed Acyclic Graph (DAG) based
on co-reference and citation logic within the first 30% of the trajectory, calculates
topological metrics (Global Connectivity and Average Branching Factor), and uses these
metrics to predict collapse.

## Requirements

- Python 3.11+
- `pip install -r requirements.txt`

## Quick Start

1. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Run the full pipeline**:
 The single entry point orchestrates the entire research flow:
 ```bash
 python code/pipeline.py --config code/config.py
 ```
 This command:
 - Downloads and validates the TELBench dataset (`NJU-LINK/TELBench`)
 - Parses trajectories and builds early-stage graphs
 - Calculates topological metrics
 - Performs stratified splitting and threshold calculation
 - Runs evaluation, sensitivity analysis, and generates the final report

3. **Outputs**:
 All processed artifacts are written to `data/processed/`:
 - `metrics.csv`: Topological metrics per trajectory
 - `train_metrics.csv`, `test_metrics.csv`: Split datasets
 - `threshold_config.json`: Primary decision threshold (20th percentile)
 - `results_report.json`: Final comprehensive report
 - `evaluation_results.json`: Structured evaluation metrics
 - `sensitivity_heatmap.png`: Visualization of sensitivity analysis
 - And more (see `data/processed/` for full list)

## Project Structure

```
.
├── code/
│ ├── config.py # Hyperparameters and configuration
│ ├── downloader.py # Dataset fetching and validation
│ ├── graph_builder.py # DAG construction from trajectories
│ ├── metrics.py # Topological metric calculation
│ ├── evaluator.py # Prediction, evaluation, and reporting
│ ├── pipeline.py # Main orchestration script
│ └──... (helper scripts)
├── data/
│ ├── raw/ # Downloaded raw dataset
│ └── processed/ # Generated artifacts (graphs, metrics, reports)
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── README.md
├── quickstart.md
├── research.md
└── requirements.txt
```

## Key Features

- **Real Data**: Uses the actual TELBench dataset from HuggingFace (`NJU-LINK/TELBench`)
- **Fail-Loudly**: The pipeline halts with descriptive errors if data sources are missing
- **Streaming**: Handles large datasets without exceeding RAM limits
- **Spec-Compliant**: Implements FR-004 (20th percentile threshold) as the primary decision boundary
- **Reproducible**: Deterministic execution with seeded RNG and cached data

## Validation

Run the test suite to verify correctness:
```bash
pytest tests/ -v
```

Run formatting and linting checks:
```bash
black --check code/
ruff check code/
```

## License

This project is part of the llmXive research initiative.
