# Quickstart: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## Prerequisites
- Python 3.11+
- Sufficient Disk Space (for derived data)
- Sufficient RAM (or use streaming mode)
- Montreal Forced Aligner (MFA) binaries and English dictionaries (for FR-022 fallback)

## Installation

1.  **Clone and Setup**:
    ```bash
    git checkout 001-semantic-collapse-threshold
    cd projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Install MFA** (for FR-022 fallback):
    ```bash
    pip install montreal-forced-aligner==2.2.0
    # Download English dictionaries
    mfa model download dictionary english
    mfa model download acoustic english_mfa
    ```

3.  **Verify Dependencies**:
    Ensure `pyroomacoustics` and `transformers` are installed:
    ```bash
    python -c "import pyroomacoustics; import transformers; print('OK')"
    ```

## Running the Pipeline

### Step 1: Data Download & Stratification
Download and prepare the stratified subset of clips.
```bash
python -m src.data.download --target-rows [SUFFICIENT_SAMPLE_SIZE] --output data/raw/stratified_subset.parquet
```

### Step 2: Validation Gate (FR-011, FR-018)
Run the validation checks before generating stress curves.
```bash
python -m src.data.validate --check-svs --check-realism
```
*If this fails, the pipeline halts.*

### Step 3: Stress Curve Generation
Generate a comprehensive set of distortion scenarios and compute metrics.
```bash
python -m src.simulation.stress_generator \
    --input data/raw/stratified_subset.parquet \
    --output data/derived/stress_curves.parquet \
    --models whisper-tiny,distil-whisper \
    --scenarios multiple
```

### Step 4: Collapse Detection
Identify the collapse points.
```bash
python -m src.analysis.collapse_detector \
    --input data/derived/stress_curves.parquet \
    --output data/derived/collapse_points.parquet
```

### Step 5: Regression & Analysis
Fit the hierarchical model and generate SHAP plots.
```bash
python -m src.analysis.regression \
    --input data/derived/collapse_points.parquet \
    --output data/derived/regression_results.json
```

## Testing

Run the unit tests to verify logic (T008):
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## Output Artifacts
- `data/derived/stress_curves.parquet`: The full stress curve dataset.
- `data/derived/collapse_points.parquet`: The identified collapse thresholds.
- `data/derived/regression_results.json`: Model coefficients and SHAP values.
