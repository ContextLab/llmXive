# Quickstart: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a Linux environment (GitHub Actions runner or local Linux/WSL).
*   **Pilot Study Access**: Ability to recruit participants or access a local dataset of human responses.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-398-the-impact-of-visual-complexity-on-cogni
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
    *Note: `requirements.txt` pins `ultralytics` and `opencv-python-headless` to ensure CPU-only operation.*

## Data Setup

1.  **Download Stimuli**:
    Run the download script to fetch a representative set of background images (or use the provided sample set if available).
    ```bash
    python code/scripts/download_stimuli.py --output data/stimuli/
    ```
    *If no script is provided, place a representative set of `.jpg` files in `data/stimuli/`.*

2.  **Verify Checksums**:
    Ensure the `data/stimuli/` directory matches the expected checksums in `state/`.

3.  **Collect Pilot Data**:
    Run the pilot study interface or ingest the collected CSV data.
    ```bash
    python code/scripts/collect_pilot_data.py --output data/measurements/raw_responses.csv
    ```
    *Note: This step requires real human participants. For CI testing, a small mock dataset of real human responses (if available) or a placeholder CSV with the correct schema must be provided.*

## Running the Pipeline

Execute the full research pipeline:

```bash
python code/main.py
```

This command performs the following steps sequentially:
1.  **Extract Metrics**: Computes entropy, variance, and object counts for all images in `data/stimuli/`.
2.  **Ingest Pilot Data**: Loads real human response data from `data/measurements/raw_responses.csv`.
3.  **Analyze**: Runs the Linear Mixed-Effects Model, applies multiple-comparison corrections, calculates FWER, and performs sensitivity analysis.
4.  **Report**: Generates `results/analysis/model_summary.json` and plots.

## Verification

1.  **Check Output Files**:
    Ensure `data/derived/stimuli_metadata.csv` and `data/measurements/raw_responses.csv` exist.
2.  **Validate Schemas**:
    ```bash
    pytest tests/contract/test_schemas.py
    ```
3.  **Review Results**:
    Open `results/analysis/model_summary.json` to verify that p-values are adjusted, FWER is reported, and VIF scores are included.

## Troubleshooting

*   **OOM Error**: If the process runs out of memory, reduce the number of stimuli in `data/stimuli/` or lower the image resolution.
*   **YOLOv8 CPU Slow**: Ensure `opencv-python-headless` is installed (not `opencv-python`) to avoid GUI dependencies that can slow down CPU inference.
*   **Missing Dependencies**: If `statsmodels` fails to import, ensure `scipy` is installed.
*   **No Pilot Data**: If `raw_responses.csv` is empty, the pipeline will fail. Ensure real data (or a valid placeholder for testing) is present.