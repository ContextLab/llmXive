# Quickstart: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Prerequisites

- Python 3.11+
- 2 vCPU, 7 GB RAM, 14 GB disk (GitHub Actions free-tier compatible)
- Git
- Internet access (for downloading datasets and models)
- Tesseract OCR (system dependency for independent validation)

## Installation

1. **Clone the repository**:
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
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Download Data

Download the OmniDoc-1 dataset and verify checksum:

```bash
python code/data/download_omnidoc.py
```

*Output*: `data/raw/omnidoc-1.parquet`

### Step 2: Preprocess & Encode

Extract crops and encode to latent vectors:

```bash
python code/data/preprocess_crops.py
python code/data/encode_latents.py
```

*Output*: `data/processed/crops.parquet`, `data/latents/latents.parquet`

### Step 3: Run Analysis

Execute the full analysis pipeline (US-01, US-02, US-03):

```bash
python code/main.py
```

*Output*: `data/metrics/results.json`, `data/images/edited_images/`, plots in `output/`

### Step 4: Validate Contracts

Verify outputs against schema contracts:

```bash
pytest tests/contract/
```

## Expected Outputs

- **Separability Report**: Accuracy, F1, p-value from permutation test, **triviality_flag**, **linearity_verified**.
- **Editing Report**: SSIM, OCR accuracy for edited images, null control comparison.
- **Robustness Report**: Sensitivity sweep plots and power analysis.
- **Visualizations**: PCA plot of latent space, edited image examples.

## Troubleshooting

- **Memory Error**: Reduce the sample size in `code/utils/config.py` (e.g., `SAMPLE_SIZE=5000`).
- **CUDA Error**: Ensure `torch` is installed in CPU-only mode (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **Dataset Not Found**: Verify internet connection and the HuggingFace URL in `code/data/download_omnidoc.py`.
- **Model Not Found**: If Qwen-Image-VAE-2.0 fails to load, the system will automatically fall back to DINOv2 (vit_base_patch14).
- **Tesseract Missing**: Install Tesseract OCR on your system to run the independent ground-truth validation.