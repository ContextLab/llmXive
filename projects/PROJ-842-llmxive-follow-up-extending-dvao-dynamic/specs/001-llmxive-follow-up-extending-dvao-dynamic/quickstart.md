# Quickstart: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-rewar"

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Experiments

### 1. Verify Theoretical Derivation
Run the symbolic math verification to ensure the theoretical bound is correct.
```bash
python src/derivation/verify_symbolic.py
```
*Output*: `data/processed/symbolic_verification.json`

### 2. Generate Synthetic Environments
Generate environments for a specific $N$ and correlation $\rho$.
```bash
python src/environment/synthetic_mdp.py --n 50 --rho 0.0 --seed 42
```
*Output*: `data/processed/noise_properties.json`

### 3. Run Full Experiment Suite
Execute the full training and analysis pipeline.
```bash
python src/main.py --config configs/default.yaml
```
*Output*:
- `data/processed/empirical_results.json`
- `data/processed/construct_validity_results.json`
- Console logs with t-test and slope analysis results.

### 4. Sensitivity Analysis (Window Size)
Run a sweep over different window sizes $k$.
```bash
python src/analysis/statistics.py --sweep window_size --values 0.01,0.05,0.1
```

### 5. Validate Construct Validity
Test different reward distributions.
```bash
python scripts/validate_construct_validity.py --distributions Linear,Sparse,Non-Convex
```

## Troubleshooting

- **Memory Error**: If the script fails with OOM, check `N`. If $N > 50$, the system should automatically reduce the state space via `reduce_state_space()`. If it still fails, reduce $N$ manually.
- **Correlation Mismatch**: If the achieved correlation in `noise_properties.json` differs significantly from the target, check the noise generation logic in `src/environment/reward_generators.py`.
- **Symbolic Verification Failure**: If `verify_symbolic.py` fails, check the algebraic derivation in `src/derivation/sample_complexity.py`.