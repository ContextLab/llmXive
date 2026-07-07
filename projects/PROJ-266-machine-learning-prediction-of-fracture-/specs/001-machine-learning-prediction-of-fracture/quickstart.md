# Quickstart: Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Prerequisites

*   Python 3.11+
*   Git
*   (Optional) A dataset containing:
    *   A CSV file with columns: `image_path`, `k_ic`, `alloy_family`.
    *   A folder containing the images referenced in the CSV.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-266-machine-learning-prediction-of-fracture-/
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
    *Note: `requirements.txt` pins CPU-only versions of PyTorch and `captum` for InputXGrad.*

## Data Preparation

### Option A: Synthetic Data (Recommended for Reproducibility)
Generate a synthetic dataset of images:
```bash
python code/data/synthetic_gen.py --output data/raw/ --count 2000
```
*Output*: `data/raw/images/` and `data/raw/labels.csv` with synthetic $K_{IC}$ values.

### Option B: User-Provided Data
Place your raw data in the `data/raw/` directory:
*   `images/`: Folder containing `.png` or `.jpg` files.
*   `labels.csv`: CSV file with columns `image_path`, `k_ic`, `alloy_family`.

*Example `labels.csv`:*
```csv
image_path,k_ic,alloy_family
images/steel_001.png,120.5,steel
images/al_002.png,45.2,al
```

## Running the Pipeline

### 1. Preprocessing
Convert images to 128x128 grayscale and split the dataset.
```bash
python code/data/preprocess.py --input data/raw/labels.csv --output data/processed/
```
*Output*: `data/processed/train/`, `data/processed/val/`, `data/processed/test/`, and `split_metadata.csv`.

### 2. Training & Evaluation
Train the CNN and baselines (5 seeds).
```bash
python code/train/train_cnn.py --data data/processed/ --seeds 5
python code/train/evaluate.py --data data/processed/ --results code/train/results.json
```
*Output*: `code/train/results.json` containing R², MAE, RMSE, and Permutation Test p-values.

### 3. Attribution & Stability
Generate InputXGrad heatmaps and check stability.
```bash
python code/explain/inputxgrad.py --model code/train/cnn_best.pt --data data/processed/test/
python code/explain/stability.py --heatmaps data/explainability/
```
*Output*: Heatmaps in `data/explainability/` and a stability report.

## Verification

Run the test suite to ensure the pipeline is working correctly:
```bash
pytest tests/
```

## Expected Output Structure

```text
data/
├── raw/
│   ├── images/
│   └── labels.csv
├── processed/
│   ├── train/
│   ├── val/
│   ├── test/
│   └── split_metadata.csv
└── explainability/
    ├── heatmap_img_001_seed_0.png
    └── stability_report.json
```
