# Quickstart: Exploring the Impact of Data Imputation Methods on Causal Inference

## Prerequisites

-   Python 3.11+
-   Git
-   7GB+ RAM (for local development; CI uses 7GB)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-047-exploring-the-impact-of-data-imputation-/
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

## Running the Simulation

### Full Sensitivity Analysis
Execute the full simulation sweep ($\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$) with 200 replications:

```bash
python code/main.py --beta-sweep --replications 200
```

### Single Run (Debug)
Run a single simulation for a specific $\beta$ value:

```bash
python code/main.py --beta 0.5 --replications 1
```

### Output
Results will be saved to `data/synthetic/`:
-   `raw/`: Generated datasets.
-   `imputed/`: Imputed datasets.
-   `estimates/`: Causal estimates and bias metrics.
-   `summary/`: Aggregated statistics and plots.

## Verification

1.  **Check Ground Truth**:
    ```bash
    python code/tests/test_scm.py
    ```
    Ensure the generated ATE matches the theoretical value.

2.  **Check MNAR Mechanism**:
    ```bash
    python code/tests/test_missingness.py
    ```
    Verify Spearman correlation $\rho > 0.5$ between $M$ and $Y$.

3.  **Run Full Test Suite**:
    ```bash
    pytest code/tests/ -v
    ```

## Troubleshooting

-   **Memory Error**: Reduce `--replications` or `sample_size` in `code/simulation/config.py`.
-   **Convergence Failure**: Increase MICE iterations or switch to Mean/KNN for debugging.
-   **Runtime Error**: Ensure no GPU acceleration is enabled (check `CUDA_VISIBLE_DEVICES` is empty).
