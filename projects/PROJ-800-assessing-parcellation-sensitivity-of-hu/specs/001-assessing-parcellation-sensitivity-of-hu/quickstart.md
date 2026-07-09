# Quickstart: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

## Prerequisites

*   Python 3.11+
*   Git
*   Sufficient free disk space (for raw data and processed matrices)
*   Sufficient RAM (recommended for smooth operation, though a defined target limit is established)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-800-assessing-parcellation-sensitivity-of-hu
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
    *Note: This installs CPU-only compatible versions of `numpy`, `scipy`, `networkx`, etc. `torch` is NOT included in the dependencies and is not used.*

## Data Setup

The pipeline is designed to download data automatically. However, if you need to manually verify the source:

1.  **Download Sample Data** (Optional, for testing):
    The `code/download_data.py` script will fetch the first 5 subjects from the OpenNeuro ds000224 by default for testing.
    ```bash
    python code/download_data.py --subjects 5 --test-mode
    ```

2.  **Full Dataset**:
    To run the full analysis (N=100):
    ```bash
    python code/download_data.py --subjects 100
    ```
    *Note: This may take significant time depending on your internet connection.*

## Running the Pipeline

Execute the main pipeline script:

```bash
python code/main.py
```

This script will:
1.  Download/verify data.
2.  Register data to MNI space if necessary.
3.  Generate adjacency matrices for AAL and Schaefer parcellations.
4.  Compute centrality metrics.
5.  Define hubs and calculate overlap.
6.  Run Spatial Spin Test.
7.  Perform sensitivity analysis (threshold sweep).
8.  Generate visualizations.

### Output Location

*   **Processed Data**: `data/processed/`
*   **Results**: `data/results/`
*   **Plots**: `data/results/plots/`

## Verification

To verify the results:

1.  **Check for missing values**:
    ```bash
    python -c "import pandas as pd; df = pd.read_csv('data/results/stats.csv'); print(df.isnull().sum())"
    ```
    *Expected: All zeros.*

2.  **Verify Hub Counts**:
    Ensure the number of hubs matches `floor(N * 0.10)`:
    *   AAL-90: multiple hubs
    *   Schaefer-200: a set of hubs
    *   Schaefer-400: a set of hubs

3.  **Run Unit Tests**:
    ```bash
    pytest tests/unit/
    ```

## Troubleshooting

*   **Memory Error**: If you encounter `MemoryError`, reduce the number of subjects in `download_data.py` or ensure you are running in the virtual environment. The pipeline processes subjects sequentially to minimize memory usage.
*   **Timeout**: If the Spatial Spin Test takes too long, edit `code/overlap.py` and reduce `n_permutations` from 1000 to 500.