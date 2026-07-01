# llmXive: Heterogeneous Scientific Foundation Model Collaboration Benchmark

## Overview
This project implements a benchmark for evaluating heterogeneous scientific foundation models across time-series, tabular, and text modalities.

## Requirements
- Python 3.11+
- pip

## Installation
```bash
# Clone the repository
git clone <repository-url>
cd PROJ-573-https-arxiv-org-abs-2604-27351

# Create virtual environment (Python 3.11)
python3.11 -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start
```bash
# Run the full benchmark with default config
python src/benchmark/run_benchmark.py --config default.yaml

# Run a single task
python src/benchmark/run_task.py --task-id T001

# Run in unified mode (text-only translation)
python src/benchmark/run_benchmark.py --config default.yaml --mode unified
```

## Project Structure
```
code/
├── src/ # Source code
│ ├── benchmark/ # Benchmark execution logic
│ ├── data/ # Data download and processing
│ ├── evaluation/ # Metrics and statistical tests
│ ├── models/ # Model wrappers and routing
│ ├── tasks/ # Task definitions and runners
│ ├── utils/ # Utility functions
│ └── validators/ # Validation agents
├── tests/ # Test suite
├── data/ # Downloaded datasets
├── state/ # Project state tracking
├── contracts/ # Schema contracts
├── requirements.txt # Dependencies
├── pyproject.toml # Project configuration
└── README.md
```

## License
Apache 2.0
