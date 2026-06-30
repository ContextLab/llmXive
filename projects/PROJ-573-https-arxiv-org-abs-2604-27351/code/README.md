# llmXive: Heterogeneous Scientific Foundation Model Collaboration Benchmark

## Overview
This project implements a benchmark for evaluating heterogeneous scientific foundation models across time-series, tabular, and text modalities.

## Prerequisites
- Python 3.11+
- pip
- git

## Quick Start

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd llmXive
 ```

2. **Setup Virtual Environment**
 ```bash
 python3.11 -m venv.venv
 source.venv/bin/activate
 ```

3. **Install Dependencies**
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify Installation**
 ```bash
 python src/benchmark/run_benchmark.py --help
 ```

## Project Structure
- `src/`: Source code
- `data/`: Dataset storage
- `tests/`: Test suite
- `state/`: Artifact tracking
- `contracts/`: Schema definitions

## Running the Benchmark
```bash
# Default heterogeneous mode
python src/benchmark/run_benchmark.py --config src/benchmark/config/default.yaml

# Unified text-only mode
python src/benchmark/run_benchmark.py --config src/benchmark/config/default.yaml --mode unified
```

## License
MIT
