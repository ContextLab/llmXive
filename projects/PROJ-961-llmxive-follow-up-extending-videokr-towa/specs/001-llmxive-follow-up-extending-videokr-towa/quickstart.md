# Quickstart: llmXive follow-up: extending "VideoKR: Towards Knowledge-Intensive Video Understandin"

## Prerequisites

*   Python 3.10+
*   Git
*   Access to the VideoKR-SFT dataset (see `research.md` for source details).
*   Adequate RAM is available (for CI or local run).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-961-llmxive-follow-up-extending-videokr-towa
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

## Data Setup

1.  **Download the dataset**:
    Place the `VideoKR-SFT` dataset files and the `knowledge_graph` file in `data/raw/`.
    *Note: If the dataset is not available via the verified URL, you must manually download it from the official VideoKR repository and place it here.*

2.  **Verify checksums** (if provided):
    ```bash
    python code/ingest/checksum.py
    ```

## Running the Pipeline

The entire analysis can be run via the main orchestrator script:

```bash
python code/main.py
```

This script performs:
1.  **Ingestion**: Loads raw data, performs entity linking, and annotates with `chain_length`.
2.  **Sampling**: Executes the two-stage pilot/oversampling strategy.
3.  **Stratification**: Calculates accuracy per hop count.
4.  **Threshold Detection**: Runs the Permutation Test for change-point detection.
5.  **Sensitivity Analysis**: Sweeps thresholds and checks for disconnection bias.
6.  **Reporting**: Generates `data/processed/threshold_results.json` and plots in `data/processed/plots/`.

## Manual Execution (Step-by-Step)

If you wish to run steps individually:

1.  **Annotate Graph**:
    ```bash
    python code/ingest/annotate_graph.py
    ```
    *Output*: `data/processed/annotated_questions.csv`

2.  **Run Analysis**:
    ```bash
    python code/analysis/detect_threshold.py
    python code/analysis/sensitivity.py
    ```
    *Output*: `data/processed/threshold_results.json`, plots.

## Verification

To verify the annotation logic:
```bash
pytest tests/unit/test_graph_utils.py
```

To verify the full pipeline (requires dataset):
```bash
pytest tests/integration/test_pipeline.py
```

## Troubleshooting

*   **Data Missing**: If the script fails with `E_DATA_MISSING`, check `data/raw/` for the required files. The pipeline does not auto-download from unverified sources.
*   **OOM Error**: If you encounter Out Of Memory errors, the two-stage sampling should handle it. If not, reduce `SAMPLE_SIZE` in `code/utils/config.py`.
*   **Entity Linking Failures**: If a high rate of `mapping_failure` is reported, check the graph schema and question text alignment.
