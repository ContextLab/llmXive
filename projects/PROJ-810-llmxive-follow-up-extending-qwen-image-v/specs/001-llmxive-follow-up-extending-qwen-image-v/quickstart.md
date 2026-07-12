# Quickstart: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Prerequisites

- Python 3.11+
- Git
- 7 GB+ RAM (free memory)
- 14 GB+ disk space

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `torch` is installed as the CPU-only version.*

## Running the Pipeline

### Step 1: Download Data
Fetch the OmniDoc dataset (verified source).
```bash
python code/data/download.py
```
*Output: `data/raw/omni-doc.parquet`*

### Step 2: Preprocess & Encode
Crop regions, extract latent vectors, and compute centroids.
```bash
python code/data/preprocess.py
```
*Output: `data/processed/latent_vectors.parquet`, `data/processed/centroids.json`*

### Step 3: Disentanglement Analysis
Train the classifier, run permutation tests, and generate PCA plots.
```bash
python code/analysis/separability.py
```
*Output: `data/interim/separability_metrics.json`, `figures/pca_plot.png`*

### Step 4: Linearity & Orthogonality Check
Validate geometric assumptions before editing.
```bash
python code/analysis/linearity_check.py
```
*Output: `data/interim/linearity_metrics.json`*
*Note: If this step fails (contamination > 15% or angle < 85), the pipeline halts.*

### Step 5: Zero-Shot Editing & Evaluation
Perform vector arithmetic, decode images, and compute SSIM/Keypoint scores.
```bash
python code/analysis/editing_eval.py
```
*Output: `data/processed/edited_images/`, `data/interim/editing_metrics.json`*

### Step 6: Statistical Validation
Apply Bonferroni correction and generate the final report.
```bash
python code/analysis/stats.py
```
*Output: `data/interim/final_report.json`*

## Verification

To verify the installation and pipeline integrity:
```bash
pytest tests/ -v --cov=code
```

## Troubleshooting

- **OOM Error**: Reduce the batch size in `code/config.py` or sample a smaller subset of the dataset.
- **CUDA Error**: Ensure `torch` is installed without CUDA support. Check `torch.cuda.is_available()` returns `False`.
- **Dataset Missing**: Verify network access to the HuggingFace URL provided in `research.md`.
- **Model Not Found**: If the specific Qwen-Image-VAE-2.0 model is not found on HuggingFace, the pipeline will halt with "Model Not Found".
- **Schema Mismatch**: If the dataset lacks required columns (bbox, modality), the pipeline will halt with "Data Schema Mismatch".
- **Linearity Fail**: If the linearity check fails, the editing pipeline halts and reports "Hypothesis Rejected: Space not linear/orthogonal".