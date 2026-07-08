# Quickstart: Multi-Property Trade-Offs in Alloy Design

## Prerequisites

*   Python 3.11+
*   Git
*   Access to HuggingFace (for dataset download)

## Installation

1.  **Clone and Setup**:
    ```bash
    git checkout 001-multi-property-trade-offs
    cd projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Download Data**:
    Run the ingestion script to fetch OQMD data:
    ```bash
    python data_ingestion.py
    ```
    *Note: This script verifies the presence of `bulk_modulus` and `shear_modulus` columns. If data is insufficient, it logs a warning and exits.*

## Running the Pipeline

Execute the full pipeline (Ingestion -> Training -> Optimization -> Analysis):

```bash
python main.py
```

### Expected Outputs

*   `data/processed/encoded.csv`: Feature-engineered dataset.
*   `data/processed/results/pareto_frontier.csv`: Synthetic trade-off curve.
*   `data/processed/results/decoupled_regions.json`: Identified low-correlation clusters.
*   `data/processed/results/figures/`: 2D plots of the Pareto frontier and decoupled regions.

## Verification

1.  **Check Data Count**: Ensure `data/processed/encoded.csv` has ≥ 500 rows.
2.  **Check Model Performance**: Verify `R²` > 0.0 (better than mean) in the console output.
3.  **Check Convex Hull**: Confirm no synthetic points in `pareto_frontier.csv` are outside the training data bounds.

## Troubleshooting

*   **Error: "Insufficient data"**: The OQMD dataset variant may lack mechanical properties. Verify the URL in `research.md` or check the raw CSV headers.
*   **Memory Error**: Ensure no other heavy processes are running; The pipeline is optimized for moderate RAM usage..