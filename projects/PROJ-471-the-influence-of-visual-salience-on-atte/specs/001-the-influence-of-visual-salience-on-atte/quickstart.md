# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended for CI compatibility)
- **Dependencies**: `pip install -r code/requirements.txt`
- **Data**: The "Moral Foundations Eye-Tracking Dataset" (ds003123) must be present in `data/raw/`.
  - *Note*: This dataset is **not** in the verified list and requires **manual download**. If automated download fails, manually download from OpenNeuro and extract to `data/raw/ds003123/`. **If data is missing, the pipeline will halt with error `DATA_MISSING_001`.**

## Installation

1.  **Clone Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-471-the-influence-of-visual-salience-on-atte
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Verify Environment**:
    ```bash
    python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
    # Expected: CUDA available: False (CPU-only mode)
    ```

## Data Setup

The pipeline expects the dataset in `data/raw/ds003123/`.
If the dataset is not present, run the download script (if public access allows):
```bash
python code/ingestion/download_data.py
```
*If this fails due to authentication, please manually download the dataset from OpenNeuro and place it in `data/raw/ds003123/`. If data is missing, the pipeline will halt with error `DATA_MISSING_001`.*

## Running the Pipeline

Execute the full pipeline:
```bash
python code/main.py
```

### Steps Executed:
1.  **Ingestion**: Downloads/verifies data. (Halt if missing)
2.  **Salience Generation**: Computes DeepGaze II maps (CPU batched).
3.  **ROI Segmentation**: Generates face/weapon masks.
4.  **Alignment**: Merges fixation data with salience scores.
5.  **Analysis**: Fits LMM/GLMM, applies FDR, runs sensitivity analysis.
6.  **Validation**: Checks output schema and resource usage.

## Output

- **Aligned Data**: `data/processed/aligned_data.csv`
- **Statistical Results**: `data/processed/results.json`
- **Logs**: `logs/pipeline.log`

## Troubleshooting

- **CUDA Error**: The pipeline is CPU-only. If you see CUDA errors, check `code/config.py` for `device="cpu"`.
- **Memory Error**: The pipeline batches images. If OOM occurs, reduce `BATCH_SIZE` in `code/config.py`.
- **Dataset Missing**: If `ds003123` is not found, ensure it is manually placed in `data/raw/`. Error `DATA_MISSING_001` will be raised.
- **Power Insufficient**: If power analysis fails, the pipeline halts with `POWER_INSUFFICIENT`.
