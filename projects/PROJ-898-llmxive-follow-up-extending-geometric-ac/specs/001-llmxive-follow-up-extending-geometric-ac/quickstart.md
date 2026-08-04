# Quickstart: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Prerequisites

- Python 3.11+
- Git
- A minimum of two CPU cores and 7 GB RAM.
- Sufficient disk space for data storage and processing.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-898-llmxive-follow-up-extending-geometric-ac
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Verify installation**:
   ```bash
   pytest tests/unit/
   ```

## Running the Pipeline

### 1. Generate Synthetic Test Set
```bash
python code/main.py --task generate --config code/config.py
```
*Output*: `data/generated/topology_shift_test_set/`

### 2. Run Baseline GAM
```bash
python code/main.py --task baseline --input data/generated/topology_shift_test_set
```
*Output*: `data/results/baseline_logs.csv`

### 3. Run Symbolic Planner
```bash
python code/main.py --task symbolic --input data/generated/topology_shift_test_set
```
*Output*: `data/results/symbolic_logs.csv`

### 4. Statistical Analysis
```bash
python code/main.py --task analyze
```
*Output*: `data/results/statistical_analysis.json`

## Validation

- **Contract Tests**: Run `pytest tests/contract/` to validate data schemas.
- **Reproducibility**: Re-run the pipeline with `--seed 42` to verify deterministic results.

## Troubleshooting

- **Physics Errors**: Check PyBullet version compatibility.
- **Out of Memory**: Reduce the number of simulation steps or topology complexity in `config.py`.
- **Latency Timeout**: If a trial exceeds a predefined time threshold, it is logged as a timeout failure.
