# Quickstart: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

## Prerequisites

-   **Python**: 3.11 or higher.
-   **System**: Linux/macOS (compatible with GitHub Actions free-tier).
-   **Dependencies**: All listed in `code/requirements.txt`.

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd specs/001-visual-distraction-cognitive-control
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
    *Note: `opencv-python-headless` is used to avoid GUI dependencies.*

## Running the Pipeline

The pipeline is executed sequentially via the scripts in `code/`.

### Step 1: Data Acquisition & Synthesis
Generates synthetic participant data and workspace images if no real data is found.
```bash
python code/01_data_acquisition.py
```
*Output*: `data/raw/participants.csv`, `data/raw/images/` (synthetic images).

### Step 2: Visual Metric Extraction
Computes edge density, color entropy, and object count.
```bash
python code/02_visual_metrics.py
```
*Output*: `data/processed/visual_metrics.csv`.

### Step 3: Statistical Analysis
Performs correlation, regression, bootstrap, and VIF checks.
```bash
python code/03_analysis.py
```
*Output*: `results/statistics.json`, `results/sensitivity/`.

### Step 4: Visualization
Generates scatter plots.
```bash
python code/04_visualization.py
```
*Output*: `results/plots/*.png`.

## Verification

Run the contract tests to ensure outputs match the schema:
```bash
pytest tests/contract/
```

## Troubleshooting

-   **OpenCV Errors**: Ensure `opencv-python-headless` is installed, not `opencv-python`.
-   **Memory Errors**: The pipeline is optimized for 7GB RAM. If OOM occurs, reduce `N` in `01_data_acquisition.py` (e.g., to 100).
-   **YOLO Failures**: If object detection fails, `object_count` will be `NaN`. The pipeline handles this by excluding those records from object-count-specific analyses.
