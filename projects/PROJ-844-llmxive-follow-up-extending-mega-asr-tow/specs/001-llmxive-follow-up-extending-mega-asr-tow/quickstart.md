# Quickstart: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## Prerequisites

*   Python 3.11+
*   Git
*   Access to Hugging Face (for dataset download).

## Installation

1.  **Clone & Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import pyroomacoustics; import transformers; import shap; print('All dependencies OK')"
    ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### 1. Download & Stratify (CPU)
```bash
python code/main.py --action download --dataset hf-audio/open-asr-leaderboard --sample-size 80
```
*Output*: `data/raw/stratified_sample.parquet`

### 2. Generate Stress Curves
```bash
python code/main.py --action distort --snr-range -10,30 --rt60-range 0.1,0.6 --models whisper-tiny
```
*Output*: `data/derived/stress_curves.parquet`

### 3. Identify Collapse Points
```bash
python code/main.py --action collapse --threshold-sss 0.5 --threshold-wer-multiplier 2
```
*Output*: `data/derived/collapse_points.parquet`

### 4. Regression & Analysis
```bash
python code/main.py --action regress --method hierarchical --interaction-check shap
```
*Output*: `data/derived/regression_results.json`, `figures/critical_vector.png`

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```
*   **Unit Tests**: Verify distortion logic, SSS calculation, collapse algorithm.
*   **Contract Tests**: Verify `stress_curves.parquet` schema matches `contracts/stress_curve.schema.yaml`.

## Troubleshooting

*   **Memory Error**: Reduce `--sample-size` or enable `--streaming` in download.
*   **CPU Timeout**: A default sample size sufficient to complete the study within 6 hours is selected. If using GPU, increase sample size.
*   **Dataset Missing**: Ensure you are using the verified HF URLs in `research.md`.
