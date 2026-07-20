# Quickstart: Single-Cell Trajectories of T-Cell Exhaustion

## Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended), 8GB+ RAM (for full dataset), 10GB+ disk.
- **Dependencies**: `wget`, `curl`, `git`.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Verify Data Access (Critical Step)**:
    *Note: This step attempts to download the four GEO datasets. If they are not publicly accessible without auth, this will fail.*
    ```bash
    python code/download_data.py --check
    ```
    *If this fails, see the "Data Availability" section in `research.md` for fallback strategies.*

## Running the Pipeline

### Option A: Full Pipeline (Single Run)
Executes download, preprocess, velocity, fork-point detection, and validation.
```bash
python code/run_pipeline.py
```
*Output*: `data/results/validation_metrics.json`, `data/results/report.html`

### Option B: Step-by-Step
1.  **Download**:
    ```bash
    python code/download_data.py
    ```
2.  **Preprocess**:
    ```bash
    python code/preprocess.py
    ```
3.  **Velocity**:
    ```bash
    python code/velocity_analysis.py
    ```
4.  **Fork-Point Detection**:
    ```bash
    python code/fork_point_detection.py
    ```
5.  **Validation**:
    ```bash
    python code/validation.py
    ```

### Option C: CI/CD (GitHub Actions)
The pipeline is configured to run automatically on push to `main` or `feature/*`.
- **Trigger**: Push to branch.
- **Runner**: `ubuntu-latest` (Free Tier).
- **Timeout**: 6 hours.

## Output Interpretation

- **`fork_points_*.csv`**: Lists genes with high divergence at branch points. `p_value` < 0.05 indicates significance.
- **`validation_metrics.json`**:
    - `spearman_correlation`: > 0.80 indicates high cross-dataset consistency.
    - `jaccard_index`: > 0.80 indicates consistent fork point identification across datasets.
    - `enrichment_p_value`: < 0.05 indicates association with therapy response.
- **`report.html`**: Interactive heatmap and summary of findings.

## Troubleshooting

- **Error: "Dataset Unavailable"**: The GEO datasets require manual download. Use `data/raw/manual/` to place downloaded files and re-run.
- **Error: "Memory Limit Exceeded"**: The dataset is too large for 7GB RAM. The pipeline will automatically subsample to 10k cells.
- **Error: "Convergence Failed"**: Velocity estimation failed. Check `logs/velocity.log` for details. The pipeline will retry with higher regularization; if it continues to fail, the dataset may be excluded from downstream analysis.
- **Error: Fabrication Detected**: Data could not be downloaded or processed. The system halted to prevent generating fake results.
