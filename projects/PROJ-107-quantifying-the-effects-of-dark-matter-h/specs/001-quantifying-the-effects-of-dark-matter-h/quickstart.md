# Quickstart: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

## Prerequisites

*   Python 3.11+
*   `git`
*   Access to the IllustrisTNG public data portal (for TNG-100).
*   (Optional) Millennium-II data access (conditional).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd specs/001-quantifying-the-effects-of-dark-matter-h
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

## Configuration

1.  **Set Data Paths**:
    Edit `code/utils/config.py` to point to your local data directory or configure the download URLs.
    ```python
    # config.py
    DATA_DIR = "data/raw"
    TNG_API_URL = "https://www.tng-project.org/api/"
    ```

2.  **Set Random Seeds**:
    Ensure reproducibility by setting the seed in `code/utils/config.py`:
    ```python
    RANDOM_SEED = 42
    ```

## Running the Pipeline

### Step 1: Ingest Data
Download and prepare the TNG-100 dataset (chunked).
```bash
python code/main.py --stage ingestion
```
*Output*: `data/raw/tng100/` contains at least one `*.hdf5` file and `data/metadata.yaml` is updated with checksums.

### Step 2: Compute Shapes & Alignments
(Placeholder – to be implemented in later tasks.)

### Step 3: Null Simulation Control
(Placeholder – to be implemented in later tasks.)

### Step 4: Statistical Analysis
(Placeholder – to be implemented in later tasks.)

### Step 5: Sensitivity Analysis
(Placeholder – to be implemented in later tasks.)

### Step 6: Generate Report
(Placeholder – to be implemented in later tasks.)

## Testing

Run the unit tests to verify tensor calculations and statistical logic:
```bash
pytest code/tests/ -v
```

## Troubleshooting

*   **Memory Error**: Reduce the chunk size in `code/utils/config.py` (e.g., `CHUNK_SIZE = 2000`).
*   **Missing Data**: Ensure you have registered with the IllustrisTNG website and have an API key set in the environment variable `TNG_API_KEY`.
*   **Millennium-II Unavailable**: If the pipeline logs "Data Gap: Millennium-II not found", the cross‑validation step is skipped. This is expected if no verified URL is provided.