# Quickstart: llmXive follow-up: extending "ViQ: Text-Aligned Visual Quantized Representations at Any Resolution"

## 1. Prerequisites

-   Python 3.11+
-   Git
-   Access to a GitHub Actions free-tier runner (or local machine with 7GB+ RAM, CPU-only).

## 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure `torch` is installed without CUDA support (e.g., `pip install torch --index-url https://download.pytorch.org/whl/cpu`).*

## 3. Data Preparation

The system automatically downloads datasets on first run if `data/raw/` is empty. To manually trigger or verify:

```bash
python code/data_loader.py --download-only
```

This will:
-   Fetch COCO and ImageNet-1K from verified URLs.
-   Save to `data/raw/`.
-   Generate checksums in `data/checksums.txt`.
-   *Note: ChestX-ray14 is not downloaded as it is out of scope.*

## 4. Running the Experiment

### Step 1: Training (Low-Res)
Train the VQ codebook on 64x64 COCO data.
```bash
python code/train.py --config code/config.py
```
*Output*: `data/results/training_metrics.json`, `code/codebook.pt`.

### Step 2: Evaluation (High-Res)
Evaluate on 1024x1024 ImageNet and COCO subset.
```bash
python code/eval.py --checkpoint code/codebook.pt
```
*Output*: `data/results/inference_metrics.json`.

### Step 3: Analysis
Compute correlations and statistical tests.
```bash
python code/analysis.py
```
*Output*: `data/results/correlation_analysis.csv`, plots in `data/results/plots/`.

## 5. Verification

Run the test suite to ensure data integrity and metric correctness:
```bash
pytest tests/ -v
```

## 6. Troubleshooting

-   **Memory Error**: The script automatically reduces sample size if memory exceeds 6GB. If manual intervention is needed, reduce `batch_size` in `code/config.py`.
-   **CUDA Error**: Ensure `torch` is the CPU version.
-   **Dataset Missing**: Check `data/raw/` for downloaded files. If ImageNet or COCO is missing, the script will fail with a clear error message.