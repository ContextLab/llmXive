# Quickstart: The Impact of Bounded Confidence on Opinion Polarization Speed

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline consists of three sequential steps. Run them in order to reproduce the study.

### Step 1: Generate Networks
Generates multiple instances of each topology (ER, BA, WS).
```bash
python code/generate_networks.py --output data/raw/networks/ --seeds 50
```

### Step 2: Run Simulations
Executes the HK model for all networks and $\epsilon$ values.
```bash
python code/simulate_hk.py \
  --networks data/raw/networks/ \
  --epsilon-start 0.05 \
  --epsilon-end 0.50 \
  --epsilon-step 0.05 \
  --seeds 50 \
  --output data/raw/simulations/
```

### Step 3: Analyze Results
Fits power laws and runs regression.
```bash
python code/analyze_scaling.py \
  --simulations data/raw/simulations/ \
  --networks data/raw/networks/ \
  --output data/processed/
```

## Verification

To verify the installation and logic:

1.  **Unit Test**:
    ```bash
    pytest tests/unit/test_hk_update.py -v
    ```
2.  **Integration Test**:
    ```bash
    pytest tests/integration/test_full_pipeline.py -v
    ```

## Troubleshooting

-   **Memory Error**: If you encounter OOM errors, reduce the number of seeds in Step 2 (e.g., `--seeds 10`). The default threshold is calibrated for the 7 GB limit.
-   **Non-convergence**: The script will flag non-convergent runs. If >10% of runs are non-convergent, check if $\epsilon$ is too low (below $\epsilon_c$).
