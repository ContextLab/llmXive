# Quickstart: Quantifying the Impact of Data Cleaning on Statistical Inference

## Prerequisites

- Python 3.11+ installed
- Access to GitHub Actions runner or local environment matching constraints (≤7 GB RAM)
- Internet access for dataset download

## Setup

1.  **Clone Repository**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for reproducibility (Constitution Principle I).*

3.  **Download Data**
    Run the acquisition script to fetch verified datasets.
    ```bash
    python acquisition.py
    ```
    *Data is saved to `data/raw/` with checksums recorded.*

4.  **Run Analysis**
    Execute the full pipeline (Cleaning → Stats → Reporting).
    ```bash
    python main.py
    ```
    *Output reports and visualizations are saved to `output/`.*

## Expected Outputs

- `data/processed/`: Cleaned dataset variants.
- `output/reports/`: JSON/CSV tables of metrics (p-values, CIs).
- `output/plots/`: PNG files (forest plot, heatmap).
- `state/`: Updated artifact hashes.

## Troubleshooting

- **Memory Error**: Reduce dataset sample size in `acquisition.py`.
- **Missing Data**: Script logs warnings for >80% missing outcome (Edge Case).
- **Runtime > 6h**: Reduce bootstrap iterations in `analysis.py` to 500.
- **Small-N Variance**: For n<50 datasets, jackknife variance estimation is used instead of bootstrap.
