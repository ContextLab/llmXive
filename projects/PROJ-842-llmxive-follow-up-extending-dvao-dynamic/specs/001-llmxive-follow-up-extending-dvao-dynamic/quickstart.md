# Quickstart: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

## Prerequisites

- Python 3.11+
- `pip` (Python package installer)
- Git

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `numpy`, `scipy`, `sympy`, `pytest`, and `pyyaml`.*

## Running the Experiment

### Full Suite
To run the complete experiment suite (N=5, 10, 20, 50, 30 runs each):
```bash
python run_experiment.py --full-sweep
```
- This will generate synthetic MDPs, run the Moving-Window Heuristic, perform statistical tests, and save results to `data/processed/empirical_results.json`.
- **Expected Duration**: ~2-4 hours on a standard CPU (GitHub Actions free-tier).

### Single Configuration
To test a specific configuration (e.g., N=10, k=0.05):
```bash
python run_experiment.py --N 10 --k 0.05 --runs 5
```

### Theoretical Derivation
To generate the theoretical derivation document:
```bash
python src/derivation/sample_complexity.py --output docs/theoretical_derivation.md
```

## Verifying Results

1. **Check Output**:
   ```bash
   cat data/processed/empirical_results.json | jq '.'
   ```
   Ensure `sample_count`, `distance_to_frontier`, and `statistical_tests` fields are populated.

2. **Run Tests**:
   ```bash
   pytest tests/ -v
   ```
   This verifies the derivation logic, environment generation, and statistical tests.

3. **Reproducibility Check**:
   Run the same command twice with the same `--seed` flag. The output JSON should be identical.

## Troubleshooting

- **Memory Error**: If the process exceeds substantial RAM usage, check the `state_space_size` in the logs. The system should have automatically degraded it. If not, reduce `--state-size` manually.
- **Convergence Failure**: If the heuristic fails to converge, check the `k` value. Ensure $k$ is large enough (minimum $k=10$ recommended).
- **Statistical Test Failure**: If $p < 0.05$ for the $\rho=0$ case, verify the noise generation logic for independence.
