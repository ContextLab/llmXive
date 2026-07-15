# PROJ-068: Evaluating the Performance of Different Data Structures in Implementing Bloom Filters

## Project Setup

This project compares the performance of different Bloom filter implementations (Array, Vector, Bitset).

### Directory Structure

The project follows this structure:

```
.
├── code/ # Source code
│ ├── benchmarks/ # Benchmarking logic
│ ├── bloom_filters/ # Bloom filter implementations
│ ├── setup_directories.py
│ └── setup_project_structure.py
├── data/ # Data storage
│ └── processed/ # Processed datasets
├── results/ # Benchmark results
│ └── benchmarks/ # CSV results and analysis
├── tests/ # Unit and integration tests
├── figures/ # Generated plots
└── specs/ # Design documents
```

### Quick Start

1. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Verify directory structure**:
 ```bash
 python code/setup_project_structure.py
 ```

3. **Run tests**:
 ```bash
 pytest tests/
 ```

4. **Run benchmarks**:
 ```bash
 python code/benchmarks/runner.py
 ```

### Task T001: Directory Structure

This task ensures the required directory structure is in place.
Run `code/setup_project_structure.py` to create or verify directories.
Run `tests/test_setup_verification.py` to verify the structure programmatically.