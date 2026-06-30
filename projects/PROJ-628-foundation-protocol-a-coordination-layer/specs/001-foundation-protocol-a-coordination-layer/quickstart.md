# Quickstart: Foundation Protocol

## Prerequisites
-   Python 3.10+
-   Git
-   Make (optional, for `make report`)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-628-foundation-protocol-a-coordination-layer/code/
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
    *Note: `requirements.txt` pins versions to ensure reproducibility (e.g., `pettingzoo==1.24.0`, `stable-baselines3==2.3.0`).*

## Running Experiments

### 1. Generate Synthetic Data (SPEAR)
```bash
python data/generate_spear.py --seeds multiple
```

### 2. Run a Single Episode (Debug)
```bash
python experiments/run_simulation.py --seed [random_seed] --task hanabi --protocol foundation
```

### 3. Run Full Experiment Suite
To run multiple seeds for all tasks and protocols (requires parallel execution):
```bash
# Run Foundation Protocol
make run-foundation

# Run Native Direct Communication (Baseline)
make run-native-direct

# Analyze results
make analyze
```

### 4. Generate Report
```bash
make report
```
This compiles `results/` into a LaTeX-style PDF and archives raw CSVs.

## Configuration

Edit `config.yaml` to adjust:
-   `num_seeds`: Number of random seeds (default: 30).
-   `crash_fraction`: Episode progress at which to inject crash (default: 0.30).
-   `alpha_levels`: Significance thresholds for sensitivity analysis (default: [0.01, 0.05, 0.10]).

## Troubleshooting

-   **ImportError: No module named 'pettingzoo'**: Ensure you activated the virtual environment.
-   **CUDA Error**: The code is CPU-only. If you see CUDA errors, check that `stable-baselines3` was installed with the CPU wheel (no `torch` CUDA version).
-   **Seed Mismatch**: Ensure `config.yaml` seeds match the `--seed` flag.