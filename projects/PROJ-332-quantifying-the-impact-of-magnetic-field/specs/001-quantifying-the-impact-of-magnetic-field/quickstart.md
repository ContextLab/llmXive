# Quickstart: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

## Prerequisites

*   Python 3.11+
*   `mdsplus` library (installed via `conda` or `pip` as per DIII-D instructions)
*   `numpy`, `scipy`, `pandas`, `matplotlib`, `pyyaml`, `pymc`
*   Access to the DIII-D public MDSplus archive (network connectivity)
*   GitHub Secrets configured for `D3D_USERNAME` and `D3D_PASSWORD`

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-332-quantifying-the-impact-of-magnetic-field
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    # Ensure mdsplus is installed separately if not in requirements.txt
    # e.g., conda install -c mdsplus mdsplus
    ```

3.  **Verify MDSplus connection**:
    ```bash
    python -c "import MDSplus; mds = MDSplus.Tree('d3d', 12345, 'readonly'); print('Connected')"
    ```

## Running the Pipeline

1.  **Prepare discharge list**:
    Create a file `discharges.txt` with up to 10 valid DIII-D discharge numbers (one per line), or ensure the manifest download URL is configured.

2.  **Set environment variables** (for local testing):
    ```bash
    export D3D_USERNAME="your_username"
    export D3D_PASSWORD="your_password"
    ```

3.  **Execute the main script**:
    ```bash
    python code/main.py --discharges discharges.txt
    ```

4.  **Check outputs**:
    *   `data/processed/analysis_ready.csv`: Validated dataset.
    *   `results/topology_vs_confinement.png`: Scatter plot.
    *   `results/correlation_results.json`: Statistical results.

## Troubleshooting

*   **MDSplus Connection Error**: The script will retry 3 times with 10s intervals. If it fails, check network connectivity to `d3d.mdsplus.org` and ensure credentials are correct.
*   **Authentication Error**: Ensure `D3D_USERNAME` and `D3D_PASSWORD` are set in the environment or GitHub Secrets.
*   **Missing Data**: Discharges with missing island width or $\tau_E$ are automatically excluded. A warning is logged.
*   **Low Power**: If the sample size is small (N < 5) or the effect size is weak, the result will be flagged as "Inconclusive due to low power".