# Quickstart: Predicting Material Stiffness from Microstructure Images

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Git (for cloning the repository)
- GB free disk space
- 7 GB RAM

## Installation

1.  **Clone the repository** (assuming you have access):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-506-predicting-material-stiffness-from-micro
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
    *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only environments.*

## Running the Pipeline

### Step 0: Governance Check
Ensure the Constitution Amendment has been applied.
- Verify `constitution.md` Principle VI allows "FFT-based numerical homogenization".
- If not, run `python code/utils/apply_constitution_amendment.py` (or follow the amendment process).

### Step 1: Generate Synthetic Data
Run the data generation script to create a sufficient number of microstructures and calculate ground truth.
```bash
python code/data/generate_microstructures.py --num-images a sufficient quantity --resolution 128 --output-dir data/raw
```
*This may take a variable duration depending on CPU speed. If it exceeds a reasonable duration threshold, the script will automatically reduce resolution to 64x64 or reduce sample size.*

### Step 2: Train the Model
Train the shallow CNN on the generated dataset.
```bash
python code/training/train.py --data-dir data/raw --epochs multiple iterations --batch-size 32
```
*This should complete within 4 hours on a standard CPU.*

### Step 3: Evaluate and Analyze
Run the evaluation script to compute metrics and perform statistical analysis.
```bash
python code/evaluation/statistical_analysis.py --model-path data/models/cnn_surrogate_v1.pt --data-dir data/raw
```
*This generates a report with MAE, R2, and t-test results.*

## Verification

- **Check Data**: Ensure `data/raw/images/` contains ≥ 2,000 files (or [deferred] if resolution fallback occurred).
- **Check Metrics**: Verify `data/processed/metrics_report.json` shows MAE ≤ 5%.
- **Check Runtime**: Confirm the full pipeline took < 6 hours.

## Troubleshooting

- **OOM Error**: Reduce `--num-images` or `--batch-size` in the training script.
- **Convergence Failure**: If FFT homogenization fails for extreme densities, the script will skip those images and log a warning.
- **CUDA Error**: Ensure `torch.cuda.is_available()` returns `False` or set `CUDA_VISIBLE_DEVICES=""` to force CPU mode.
- **Constitution Error**: If the pipeline fails due to governance constraints, check `constitution.md` and ensure Principle VI has been amended.
