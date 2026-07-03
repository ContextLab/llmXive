# Quickstart: Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic Glasses

## Prerequisites

*   Python 3.11+
*   A valid Materials Project API key (optional, for automated download)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Set the Materials Project API key as an environment variable (optional):
```bash
export MP_API_KEY="your_api_key_here"
```
*If not set, the pipeline will automatically generate a verified synthetic dataset.*

## Running the Pipeline

Execute the full pipeline (Ingest $\rightarrow$ Train $\rightarrow$ Evaluate $\rightarrow$ Visualize) via Make:

```bash
make all
```

### Individual Steps

*   **Download/Generate Data**:
    ```bash
    make ingest
    ```
    *This step attempts to fetch from Materials Project API. If unavailable, it generates a synthetic dataset and records checksums.*
*   **Train Models**:
    ```bash
    make train
    ```
*   **Evaluate & Plot**:
    ```bash
    make evaluate
    ```

## Expected Outputs

After running `make all`, check the `data/artifacts/` directory:
*   `metrics.json`: Performance of all models (including Ridge and Wilcoxon p-values).
*   `plots/`:
    *   `correlation_heatmap.png`: Descriptor vs. Shear Modulus.
    *   `pdp_top3.png`: Partial Dependence Plots.
    *   `feature_importance.png`: Permutation importance ranking.
*   `state/...yaml`: Checksums of raw data.

## Troubleshooting

*   **Error: "Element X not found in Mendeleev"**: The dataset contains hypothetical elements. These rows are automatically dropped.
*   **Data Source**: If no real data is found, the pipeline will automatically switch to the **Synthetic Dataset** mode. Check the logs for "Using Synthetic Fallback".
