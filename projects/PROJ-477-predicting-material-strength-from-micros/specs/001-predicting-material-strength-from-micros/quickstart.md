# Quickstart: Predicting Material Strength from Microstructure Images

## Prerequisites

- Python 3.11 or higher
- Git
- GB free disk space
- GB RAM (minimum)

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd projects/PROJ-477-predicting-material-strength-from-micros
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Preparation

1.  **Download and Validate Data**
    ```bash
    python code/data/download.py
    python code/data/validate.py
    ```
    This will download the EBSD dataset from the verified Zenodo source and verify its checksum.

2.  **Preprocess Data**
    ```bash
    python code/data/preprocess.py
    ```
    This will resize images to 224×224, normalize them, split them into train/validation/test sets, and extract grain size features.

## Training

Run the training script:
```bash
python code/models/trainer.py
```
This will train the MobileNetV2 model with early stopping and save the best checkpoint to `code/models/checkpoints/best_model.pth`.

## Evaluation

Run the evaluation script:
```bash
python code/eval/evaluator.py
```
This will compute MSE, R², perform the paired t-test against the baseline, and generate `results/null_hypothesis_report.json`.

## Interpretability & Sensitivity

1.  **Generate Grad-CAM Heatmaps**
    ```bash
    python code/eval/interpretability.py --mode gradcam
    ```
    Heatmaps will be saved to `results/heatmaps/`.

2.  **Sensitivity Analysis**
    ```bash
    python code/eval/interpretability.py --mode sensitivity
    ```
    Results will be saved to `results/sensitivity_report.json`.

3.  **Confidence Intervals**
    ```bash
    python code/eval/predictor.py
    ```
    Predictions with confidence intervals will be saved to `results/predictions.csv` (FR-008).

## Verification

1.  **Run Unit Tests**
    ```bash
    pytest tests/unit/
    ```

2.  **Lint Code**
    ```bash
    ruff check code/ --fix
    ```

3.  **Check Memory Profile**
    ```bash
    python code/utils/memory_profiler.py --stress-test
    ```
    Ensure peak memory usage remains within acceptable system constraints.