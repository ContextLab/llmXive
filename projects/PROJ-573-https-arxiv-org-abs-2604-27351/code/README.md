# llmXive: Heterogeneous Scientific Foundation Model Collaboration Benchmark

A Python 3.11 project for benchmarking heterogeneous scientific foundation models across time-series, tabular, and text modalities.

## Quick Start

1. **Initialize the project**:
 ```bash
 python setup_project.py
 ```

2. **Activate the virtual environment**:
 ```bash
 source.venv/bin/activate # Linux/macOS
.venv\\Scripts\\activate # Windows
 ```

3. **Run the benchmark**:
 ```bash
 python code/src/benchmark/run_benchmark.py --config code/src/benchmark/config/default.yaml
 ```

## Project Structure

```
.
├── code/
│ ├── src/ # Source code
│ ├── tests/ # Test suite
│ ├── data/ # Dataset storage
│ ├── state/ # State tracking
│ └── contracts/ # Schema contracts
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration
└── README.md
```

## Requirements

- Python 3.11+
- pip

## License

Apache 2.0