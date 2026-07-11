# Quickstart: llmXive follow-up: extending EVA-Bench

## Prerequisites

*   Python 3.11+
*   `ffmpeg` (system package, required by `librosa`)
*   Access to the EVA-Bench dataset (or synthetic generation capability)

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    cd projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import librosa; import statsmodels; print('Dependencies OK')"
    ```

## Data Preparation

1.  **Download EVA-Bench**:
    *   Place raw audio files in `data/raw/`.
    *   Ensure `data/checksums.json` is updated with the checksums of the raw files.
    *   *Note*: If raw files are missing, run `python code/main.py --mode synthetic` to generate synthetic audio.

2.  **Verify Data Integrity**:
    ```bash
    python code/main.py --mode verify-data
    ```

## Running the Pipeline

### 1. Generate Perturbations
Run the latency and acoustic injection pipeline:
```bash
python code/main.py --mode inject --config config/perturbation_config.yaml
```
*   This will generate perturbed audio files in `data/processed/audio/`.

### 2. Re-evaluate Scores
Run the EVA-Bench evaluation on perturbed files:
```bash
python code/main.py --mode evaluate
```
*   Output: `data/processed/results.csv`.

### 3. Statistical Analysis
Run the LMM and segmented regression:
```bash
python code/main.py --mode analyze
```
*   Output: `data/processed/threshold_models.json` and plots in `data/processed/figures/`.

### 4. Full Pipeline (CI Mode)
To run the entire pipeline in one go (suitable for CI):
```bash
python code/main.py --mode full --seed 42
```

## Configuration

Edit `config/perturbation_config.yaml` to adjust:
*   Latency range (200ms–2000ms).
*   Jitter parameters.
*   Acoustic SNR levels.
*   Random seed.

## Troubleshooting

*   **OOM Error**: Ensure `code/injectors/latency.py` is using chunked processing. Check RAM usage.
*   **EVA-Bench Error**: Verify that the original EVA-Bench code is compatible with the current Python environment.
*   **Timeout**: If the pipeline exceeds 6 hours, reduce the number of latency levels in the config.

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```
