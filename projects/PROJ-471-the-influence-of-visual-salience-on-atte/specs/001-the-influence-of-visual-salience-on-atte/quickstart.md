# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face (for dataset download)
- 7 GB RAM (minimum)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-471-the-influence-of-visual-salience-on-atte
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

## Running the Pipeline

### Step 1: Download Data
Fetch the OpenNeuro dataset (streaming mode to save disk):
```bash
python code/ingestion/download_data.py
```
*This will create `data/raw/` with checksums.*

### Step 2: Generate Salience Maps
Run DeepGaze II on the stimulus images:
```bash
python code/ingestion/salience_gen.py --cpu
```
*Output: `data/processed/salience_maps/`*

### Step 3: Extract Fixation Metrics & Align
Parse eye-tracking data and merge with salience:
```bash
python code/processing/eye_tracking.py
python code/processing/segmentation.py  # If masks needed
```
*Output: `data/interim/aligned_trials.csv`*

### Step 4: Statistical Analysis
Fit LMM and perform sensitivity analysis:
```bash
python code/analysis/lmm_fit.py
python code/analysis/robustness.py
```
*Output: `data/processed/analysis_results.json`*

## Verification

Run the test suite to ensure integrity:
```bash
pytest tests/ -v
```

## Troubleshooting

- **RAM Error**: If `MemoryError` occurs during salience generation, reduce the image resolution in `code/config.py` (e.g., `IMAGE_SIZE = 160`).
- **CUDA Error**: If DeepGaze II attempts to use CUDA, ensure `--cpu` flag is set. The pipeline will automatically fall back to CPU.
- **Missing Masks**: If YOLOv8 fails to detect "weapons", the script will log a warning and proceed with "other" or skip the ROI.
