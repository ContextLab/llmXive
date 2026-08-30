# Quickstart: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Prerequisites
- Python 3.11+
- 2 vCPU, 7 GB RAM (or access to a Kaggle GPU for the escape hatch).
- Internet connection (for dataset streaming).

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/requirements.txt
   ```

## Running the Pipeline

### 1. Data Download & Preprocessing
The pipeline streams the dataset automatically. No manual download is required.
```bash
python projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/src/main.py --phase data_load
```

### 2. Latent Extraction & Disentanglement Analysis
Runs the encoding, SVM training, and permutation test.
```bash
python projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/src/main.py --phase disentanglement
```

### 3. Zero-Shot Editing
Performs vector arithmetic and generates edited images.
```bash
python projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/src/main.py --phase editing
```

### 4. Full Run (End-to-End)
Executes all phases in order.
```bash
python projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/code/src/main.py --full
```

## Output Verification
- Check `data/results/metrics.json` for accuracy, F1, SSIM, and Keypoint scores.
- Check `data/results/plots/` for PCA visualizations and edited image examples.
- Verify that `p_value` < 0.05 (Bonferroni corrected) for primary findings.

## Troubleshooting
- **OOM Error**: If the process runs out of memory, the script will automatically reduce the batch size or trigger the GPU escape hatch (if configured).
- **Dataset Error**: Ensure internet connectivity. If the Hugging Face dataset is inaccessible, the script will exit with a clear error message.