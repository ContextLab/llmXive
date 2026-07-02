# llmXive: Heterogeneous Scientific Foundation Model Collaboration Benchmark

This project implements a benchmark for evaluating heterogeneous scientific foundation models across time-series, tabular, and text modalities.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Create Virtual Environment

```bash
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -m src.benchmark.run_benchmark --help
```

## Project Structure

```
.
├── code/
│ ├── src/ # Source code
│ │ ├── benchmark/ # Benchmark execution scripts
│ │ ├── data/ # Data handling utilities
│ │ ├── evaluation/ # Metrics and statistical tests
│ │ ├── models/ # Model wrappers and routing
│ │ ├── tasks/ # Task definitions and runners
│ │ ├── utils/ # Utilities (logging, checksums, etc.)
│ │ └── validators/ # Validation agents
│ ├── tests/ # Test suites
│ ├── data/ # Downloaded datasets and outputs
│ ├── state/ # Project state and hashes
│ ├── contracts/ # Schema contracts
│ ├── research/ # Research verification scripts
│ ├── requirements.txt # Python dependencies
│ ├── pyproject.toml # Project configuration
│ └── README.md # This file
└──...
```

## Running the Benchmark

### Full Benchmark (Heterogeneous Mode)

```bash
python -m src.benchmark.run_benchmark --config src/benchmark/config/default.yaml
```

### Unified Mode (Text-Only Translation)

```bash
python -m src.benchmark.run_benchmark --config src/benchmark/config/default.yaml --mode unified
```

### Single Task Execution

```bash
python -m src.benchmark.run_task --task-id T001
```

## Configuration

Default configuration is located in `src/benchmark/config/default.yaml`. Modify this file to change:
- Datasets to evaluate
- Models to use
- Number of seeds
- Timeouts
- Output paths

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest`
4. Submit a pull request

## License

MIT License
