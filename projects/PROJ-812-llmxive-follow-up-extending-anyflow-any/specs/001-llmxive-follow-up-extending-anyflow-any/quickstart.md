# Quickstart: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Prerequisites

- Python 3.11+
- 7GB+ RAM
- Internet access (for dataset download)
- Manual annotation capability (or pre-prepared CSV)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will pin CPU-only versions of `torch` and `onnxruntime`.*

## Data Preparation

### Step 1: Download Videos
Run the download script to fetch and stratify videos:
```bash
python code/data_download.py --download --stratify --output-dir data/raw/videos
```
*This will fetch a representative set of clips ([deferred] cuts) from UCF101, Kinetics, DAVIS.*

### Step 2: Manual Annotation
**Important**: You must manually annotate the videos.
1.  Open the downloaded videos in `data/raw/videos/`.
2.  Assign a score to each clip based on temporal continuity.
3.  Save the scores in `data/raw/continuity_scores.csv` with columns: `video_id`, `score`.

*Alternatively, use the provided `data/raw/continuity_scores_sample.csv` for testing, or run the annotation interface script:*
```bash
python code/annotation_interface.py --input-dir data/raw/videos --output-file data/raw/continuity_scores.csv
```

## Execution

### Run the Full Pipeline
Execute the main pipeline script:
```bash
python code/main_pipeline.py
```
*This script will:*
1.  **Preflight**: Check runtime on a sample of clips.
2.  **Inference**: Compute divergence scores for all clips (CPU-only).
3.  **Analysis**: Perform correlation and sensitivity analysis.
4.  **Report**: Generate `variance_report.csv`, `correlation_results.csv`, `sensitivity_report.csv`, and `final_report.md`.

### Check Results
View the final outputs in `data/processed/`:
- `divergence_scores.csv`: Computed metrics.
- `correlation_results.csv`: Pearson/Spearman coefficients.
- `sensitivity_report.csv`: Threshold analysis.
- `variance_report.csv`: Variance check results.
- `final_report.md`: Final narrative report.

## Troubleshooting

- **Runtime Exceeded**: If the preflight check fails, the script will reduce Euler steps to N=200 or halt.
- **Memory Error**: Ensure no other heavy processes are running. The script processes clips sequentially.
- **Variance Error**: If `variance < 0.05`, the script will halt. Re-check your manual annotations to ensure a mix of scores.
- **Model Source Missing**: If the AnyFlow model is not found at the verified URL, the script will halt with a "Blocked" status.