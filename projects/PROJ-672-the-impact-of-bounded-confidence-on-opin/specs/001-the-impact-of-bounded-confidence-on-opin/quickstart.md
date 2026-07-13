# Quickstart: The Impact of Bounded Confidence on Opinion Polarization Speed

## Prerequisites

-   Python 3.11+
-   `pip` (Python package manager)
-   Git

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    cd projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is designed to run end-to-end via the `main.py` script.

### 1. Generate Networks
Generates an ensemble of networks per topology type.
```bash
python code/generate_networks.py --output data/raw/network_metrics.csv --seeds 50
```

### 2. Run Simulations
Executes the HK model sweep. **Note**: This may take up to 2-3 hours.
```bash
python code/simulate_hk.py \
  --networks data/raw/network_metrics.csv \
  --output data/raw/simulations.csv \
  --eps 0.05 0.50 0.05 \
  --max-iter 10000
```

### 3. Analyze Scaling
Fits power laws and runs regressions using the two-stage estimation method.
```bash
python code/analyze_scaling.py \
  --simulations data/raw/simulations.csv \
  --networks data/raw/network_metrics.csv \
  --output data/processed/
```

### 4. Sensitivity Analysis (Optional)
Tests robustness of $\gamma$ to convergence threshold.
```bash
python code/sensitivity_analysis.py \
  --simulations data/raw/simulations.csv \
  --output data/processed/sensitivity_results.csv
```

### 5. Generate Checksums
Generates `data/.checksums.json` and updates the state file.
```bash
python code/utils/checksums.py --data-dir data/ --state-file state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml
```

## Verification

To verify the results:
1.  Check `data/processed/scaling_results.csv` for `model_type` and `r_squared`.
2.  Check `data/processed/regression_results.csv` for `fdr_adjusted_p` values < 0.05.
3.  Run the test suite:
    ```bash
    pytest tests/
    ```

## Troubleshooting

-   **Memory Error**: Ensure you are not holding all simulation states in memory. The scripts stream to disk.
- **Timeout**: If a simulation hangs, check the `max-iter` flag. The default is [deferred].
-   **Non-convergence**: If many runs are `non_converged`, the $\epsilon$ range might be too close to $\epsilon_c$. The analysis will handle this by flagging the model as `inconclusive`.
-   **Model Mismatch**: If `model_type` is `exponential` for most topologies, the power-law hypothesis may be rejected for this dataset.
