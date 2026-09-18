# Quickstart: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Prerequisites

-   Python 3.11+
-   HCP Access Credentials (if using full HCP dataset) or a public dataset subset.
-   7 GB RAM, 14 GB Disk.

## Installation

1.  **Clone Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-331-investigating-the-influence-of-network-m
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Configuration

1.  **Set Environment Variables**:
    ```bash
    export HCP_ACCESS_KEY="your_key_here"  # If required
    export PYTHONHASHSEED=42
    ```

2.  **Verify Data Paths**:
    Ensure `config.py` points to the correct `data/raw/` and `data/processed/` directories.

## Running the Pipeline

1.  **Execute Main Script**:
    ```bash
    python code/main.py
    ```
    This will:
    -   Download data (if not present).
    -   Preprocess connectomes.
    -   Compute motif z-scores.
    -   Run statistical analysis (multivariate regression, VIF check).
    -   Generate `results/results.pdf`.

2.  **Check Logs**:
    Review `data/logs/pipeline.log` for warnings (e.g., skipped subjects).

3.  **View Results**:
    Open `results/results.pdf` to see scatter plots, correlations, and power analysis.

## Testing

Run unit and integration tests:
```bash
pytest tests/
```

## Troubleshooting

-   **Missing Data**: If a subject is skipped, check `pipeline.log` for "Missing diffusion data" warnings.
-   **Timeout**: If motif enumeration exceeds 300s, reduce the number of subjects or check CPU load.
-   **Import Error**: Ensure `venv` is activated and `requirements.txt` is up to date.