# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Anticipatory Reward Processing

## Prerequisites

- **Python**: 3.11+
- **System**: Linux (GitHub Actions runner or local equivalent).
- **Disk Space**: 15 GB (for raw data and processing).
- **RAM**: 8 GB (recommended for smooth operation, 7 GB minimum).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-491-investigating-the-relationship-between-b
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

## Running the Pipeline

The pipeline is executed via the `main.py` script located in `code/`.

1.  **Execute the full pipeline**:
    ```bash
    python code/main.py
    ```
    *This will:*
    - Download data for 50 subjects (or fail if <50 available).
    - Preprocess and extract time series.
    - Calculate flexibility scores.
    - Perform correlation analysis and sensitivity tests.
    - Generate `paper/results.md`.

2.  **Run specific modules (for debugging)**:
    - **Ingestion only**: `python code/main.py --step ingest`
    - **Preprocessing only**: `python code/main.py --step preprocess`
    - **Analysis only**: `python code/main.py --step analyze`

## Verifying Results

1.  **Check Output Files**:
    - `data/processed/flexibility_scores.csv`
    - `data/processed/correlation_results.csv`
    - `paper/results.md`

2.  **Validate Report Content**:
    - Open `paper/results.md`.
    - Ensure it contains the phrase "associational relationship".
    - Ensure it does **not** contain the word "causal".

3.  **Run Tests**:
    ```bash
    pytest tests/
    ```

## Troubleshooting

- **Error: "Insufficient data"**: The verified HCP sources contain a limited number of subjects with both scan types. The pipeline terminates as per FR-010.
- **Error: "Memory limit exceeded"**: Ensure no other heavy processes are running. The script is designed to stream data, but 8 GB RAM is recommended.
- **Error: "Session mismatch"**: A subject's resting and task scans share the same session ID. The subject is skipped (FR-008).
