# Quickstart: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

## Prerequisites

- **Python**: 3.11+
- **System**: Linux (or WSL2) with 2+ CPU cores, 7GB+ RAM.
- **Dataset**: The `AlayaWorld` dataset. **Note**: As of this writing, no verified public URL exists. You must provide the dataset locally or via a custom loader. If unavailable, the pipeline will run in "Mock Mode" for *unit testing* only, and the primary research question cannot be answered.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to a CPU-only build (`torch --index-url https://download.pytorch.org/whl/cpu`).*

4.  **Prepare Data**:
    - If you have the AlayaWorld dataset, place it in `data/raw/alaya_world/`.
    - If not, the system will automatically generate mock data for *unit testing* (CV pipeline validation, symbolic engine logic).
    - **Ground Truth**: Create `data/annotations/ground_truth_50.json` manually or via the provided script if the dataset is available.

## Running the Pipeline

### 1. Ground Truth Validation (FR-007)
Before running the full experiment, validate the CV pipeline on a small subset.
```bash
python code/main.py --mode validate --subset-size 50
```
- **Expected Output**: `data/results/cv_validation.json` with `validation_status: valid` (if accuracy ≥ 85%).
- **Action**: If `invalid`, adjust optical flow parameters in `code/cv_pipeline.py`.

### 2. Feasibility Gate
If the dataset is unavailable or CV validation fails, the pipeline will abort and output a "Methodological Validation" report.

### 3. Baseline Run (US-1)
Generate baseline videos and calculate drift scores.
```bash
python code/main.py --mode baseline --seeds 10 --sequences-per-seed 10
```
- **Output**: `data/results/baseline_scores.json`.

### 4. Hybrid Run (US-2)
Run the hybrid correction loop.
```bash
python code/main.py --mode hybrid --seeds 10 --sequences-per-seed 10
```
- **Output**: `data/results/hybrid_scores.json`.

### 5. Statistical Analysis (US-1, US-2)
Compare baseline and hybrid results.
```bash
python code/main.py --mode analyze --compare baseline hybrid
```
- **Output**: `data/results/statistical_report.json` containing p-values and Shapiro-Wilk test results.

### 6. Resource Monitoring
Resource metrics are logged automatically during every run.
- **View Logs**: `cat data/results/resource_logs.json`

## Troubleshooting

- **Memory Error (OOM)**: The pipeline is designed for standard RAM configurations. If you hit OOM, ensure no other heavy processes are running and that `streaming=True` is used in the dataset loader.
- **Slow Execution**: The time limit is tight. Ensure you are using a CPU with at least 2 cores. If using a cloud runner, check for CPU throttling.
- **CV Accuracy Low**: If the validation accuracy is < 85%, check the `data/raw/` images for quality. Adjust the optical flow parameters in `code/cv_pipeline.py`.
