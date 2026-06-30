# KVarN Variance-Normalized KV-Cache Quantization

Automated research pipeline for implementing and evaluating KVarN quantization on LLMs.

## Prerequisites

- Python 3.10+
- CPU-only environment (No CUDA required for this research scope)

## Installation

1. Clone the repository.
2. Navigate to the `code/` directory.
3. Install dependencies:

```bash
cd code
pip install -r requirements.txt
```

## Project Structure

- `src/`: Source code for quantizers, inference hooks, and analysis.
- `tests/`: Unit and integration tests.
- `data/raw/`: Directory for downloaded datasets (MATH500, AIME, etc.).
- `data/processed/`: Directory for generated logs, results, and plots.
- `specs/`: Design documents and requirements.
- `contracts/`: Schema definitions for data outputs.

## Usage

### Running Benchmarks

```bash
python run_benchmark.py --model microsoft/phi-2 --dataset math_dataset --quantizer kvarn
```

### Running Analysis

```bash
python run_analysis.py
```

## Development

- Formatting: `black code/`
- Linting: `ruff check code/`
- Testing: `pytest tests/`

## License

Research Project - All rights reserved.
