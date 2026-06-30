# Quickstart: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

## Prerequisites

- Python 3.10+
- Git
- Access to GitHub Actions (for CI) or a local environment with similar specs (≤6GB RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-228-investigating-the-impact-of-visual-compl
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
    The `code/ingestion.py` script will download the OpenNeuro dataset **ds000248** (Naturalistic Viewing). Ensure you have sufficient disk space (>14GB).

    ```bash
    python code/ingestion.py --dataset ds000248
    ```

2.  **Verify data integrity**:
    Checksums will be automatically recorded in `data/metadata.yaml`. The script will also verify the presence of stimulus images and check for pre-residualization flags in the BOLD data.

## Running the Pipeline

To run the entire pipeline (ingestion, processing, analysis):

```bash
python code/main.py
```

This will:
1.  Download and verify the dataset.
2.  Compute visual complexity metrics, luminance, and contrast.
3.  Extract DLPFC time-series.
4.  Fit subject-level GLMs with AR(1) pre-whitening.
5.  Perform group-level analysis and permutation tests.
6.  Save results to `data/results/`.

## Running Individual Stages

- **Ingestion only**:
    ```bash
    python code/ingestion.py
    ```
- **Complexity calculation**:
    ```bash
    python code/complexity.py
    ```
- **ROI extraction**:
    ```bash
    python code/roi_extraction.py
    ```
- **Modeling**:
    ```bash
    python code/modeling.py
    ```

## Testing

Run the test suite:

```bash
pytest tests/
```

## Troubleshooting

- **Memory Error**: If you encounter a memory error, ensure you are not running other heavy processes. The pipeline is designed to process data in chunks.
- **Dataset Unavailable**: If the OpenNeuro dataset is unavailable, the script will fail with a clear error message. Check your internet connection and the dataset URL.
- **Collinearity Warning**: If VIF is high, the pipeline will automatically switch to separate univariate models and log this decision.