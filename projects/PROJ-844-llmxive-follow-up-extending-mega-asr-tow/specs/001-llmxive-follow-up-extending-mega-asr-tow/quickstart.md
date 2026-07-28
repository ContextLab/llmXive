# Quickstart: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## 1. Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace Hub (for dataset streaming)
- Substantial disk space (for cached datasets and derived artifacts)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd <project-root>

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Key Dependencies**:
- `datasets`: For streaming HuggingFace datasets
- `transformers`: For ASR models and embeddings
- `scikit-learn`: For regression analysis
- `jiwer`: For WER calculation
- `librosa`, `pyroomacoustics`: For audio distortion
- `scipy`: For sigmoid and linear curve fitting
- `pytest`: For testing

## 3. Configuration

Edit `src/lib/config.py` to set:
- `SEED`: Random seed for reproducibility (default: 42)
- `DATA_DIR`: Path to `data/` directory
- `SUBSET_SIZE`: Number of audio clips to process (e.g., 500)
- `MODELS`: List of ASR models to test (e.g., `["whisper-tiny", "distil-whisper"]`)

## 4. Running the Pipeline

### Step 1: Download & Stratify Data
```bash
python -m src.cli.main --task download --subset-size [qualitative magnitude]
```
This streams the verified datasets, performs stratified random sampling, **splits clips into train/test sets**, and saves to `data/raw/`.

### Step 2: Generate Stress Curves
```bash
python -m src.cli.main --task stress-test --models whisper-tiny,distil-whisper
```
Applies multiple distortion vectors per clip, computes SSS and WER, saves to `data/derived/stress_curves.parquet`.

### Step 3: Fit Curves & Detect Collapse
```bash
python -m src.cli.main --task fit-curves --models whisper-tiny,distil-whisper
python -m src.cli.main --task detect-collapse --threshold 0.5 --wer-factor 2.0
```
Fits **both linear and sigmoid models**, selects the best fit, extracts the slope (SSD) and Area Under Stress Curve (AUSC), and identifies collapse points, saves to `data/derived/collapse_points.parquet`.

### Step 4: Train Regression Model
```bash
python -m src.cli.main --task regress --interaction-term
```
Trains the regression model (predicting SSD/AUSC from SNR/RT60), outputs coefficients and metrics to `data/derived/regression_results.json`.

### Step 5: Sensitivity Analysis
```bash
python -m src.cli.main --task sensitivity --thresholds 0.40,0.45,0.50,0.55,0.60
```
Sweeps thresholds and reports variance in critical interaction vectors.

## 5. Validation

Run unit and integration tests:
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

Validate output schemas:
```bash
pytest tests/contract/ -v
```

**Note**: Ensure `tests/unit/` contains `__init__.py` and `test_distortion.py`, `test_metrics.py`, `test_curve_fit.py`. Ensure `pytest.ini` is present in the root.

## 6. Output Artifacts

- `data/derived/stress_curves.parquet`: Full stress curve data
- `data/derived/collapse_points.parquet`: Identified collapse intensities (for sensitivity analysis)
- `data/derived/regression_results.json`: Model coefficients and metrics (SSD/AUSC prediction)
- `reports/sensitivity_analysis.md`: Sensitivity analysis results

## 7. Troubleshooting

- **OOM Error**: Reduce `SUBSET_SIZE` in `config.py` or enable streaming explicitly.
- **ASR Model Load Failure**: Ensure `transformers` is up-to-date; try `whisper-tiny` only.
- **Dataset Download Slow**: Use `HF_DATASETS_OFFLINE_MODE=1` if re-running locally with cached data.
