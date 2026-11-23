# Quickstart: Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Prerequisites
- Python 3.11+
- Git
- Access to a Linux environment (GitHub Actions or local Linux)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-266-machine-learning-prediction-of-fracture-
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### 1. Generate Synthetic Data
Since no open real-world dataset for metallic alloy fracture toughness is available in the verified sources, the pipeline uses a synthetic generator to **simulate the upload scenario** described in User Story 1.
```bash
cd code
python data/synthetic_gen.py --output-dir ../data/raw --n-images [qualitative_quantity]
```
*This generates 2,000 synthetic microstructure images and a `metadata.csv`, simulating the upload of a real dataset.*

### 2. Preprocess Data
```bash
python data/preprocess.py --input-dir ../data/raw --output-dir ../data/processed
```
*This resizes images to 128x128, normalizes, and splits them into train/val/test sets stratified by alloy family.*

### 3. Train Models
```bash
python models/train.py --data-dir ../data/processed --seeds 0 1 2 3 4
```
*Trains the CNN and baselines for multiple seeds. Outputs `results.json`.*

### 4. Evaluate and Attribute
```bash
python eval/attribution.py --model-path ../models/cnn_best.pth --data-dir ../data/processed/test
python eval/stability.py --heatmaps-dir ../data/explainability/heatmaps
```
*Generates Grad-CAM heatmaps and calculates IoU stability scores.*

## Verification
Run the test suite to ensure the pipeline is functioning correctly:
```bash
pytest tests/
```
*Expected output: All tests pass, including split validation and model architecture checks.*

## Troubleshooting
- **Memory Error**: Ensure you are not loading the entire dataset into memory at once. Use streaming or batch processing.
- **CUDA Error**: The pipeline is CPU-only. If you see CUDA errors, check `code/models/cnn.py` to ensure `device="cpu"` is set.
- **Missing Data**: If `data/raw` is empty, re-run `synthetic_gen.py`.