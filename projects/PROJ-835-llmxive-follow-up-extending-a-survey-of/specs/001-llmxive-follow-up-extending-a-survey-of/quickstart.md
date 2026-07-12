# Quickstart: LlmXive Follow-up: Latent-Space Jailbreak Detection

## Prerequisites

- **Python**: 3.11+
- **Hardware**: CPU-only environment (2 cores, 7 GB RAM). **No GPU required.**
- **Dataset**: A verified audio dataset containing `jailbreak` and `benign` samples.
  - **CRITICAL**: The current "Verified datasets" list contains only text data. You **MUST** provide a valid audio dataset path or add a verified audio URL to the project configuration. If no verified audio dataset is found, the pipeline will **HALT** with a `FATAL: Missing Verified Audio Dataset` error.

## Installation

1. **Clone the repository** (if not already done).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-835-llmxive-follow-up-extending-a-survey-of/code/requirements.txt
   ```
   *Dependencies include*: `torch`, `transformers`, `librosa`, `scikit-learn`, `pandas`, `numpy`.

## Configuration

Edit `code/config.py` to set the following:
- `DATASET_PATH`: Path to your audio dataset (Parquet/CSV) or HuggingFace dataset name.
- `EMBEDDING_MODEL`: `"distil-whisper-base"` (default).
- `OUTPUT_DIR`: Path to save embeddings and results.
- `SEED`: Random seed (default: 42).

## Execution Steps

### Step 1: Download & Verify Data
*Note: If using HuggingFace, this runs automatically. If using local files, ensure checksums match.*
```bash
python code/data/download.py
```
*Note*: This step will fail if no verified audio dataset is found.

### Step 2: Extract Embeddings
*This step may take several hours depending on dataset size. It is CPU-bound.*
```bash
python code/data/extract.py
```
*Output*: `data/embeddings/embeddings.npy`, `data/embeddings/labels.npy`.

### Step 3: Train & Evaluate
*Runs training, sensitivity analysis, and McNemar's Test.*
```bash
python code/models/train.py
python code/models/eval.py
```
*Output*: `results/metrics.json`, `results/predictions.csv`.

### Step 4: Verify Results
Check `results/metrics.json` for:
- `recall`: Must be > random baseline.
- `p_value`: Must be < 0.05 (from McNemar's Test).
- `threshold_sensitivity`: Verify stability across {0.3, 0.5, 0.7}.
- `auc_roc`: Should be > 0.5 (better than random).

## Troubleshooting

- **FATAL: Missing Verified Audio Dataset**: You must provide a valid audio dataset. Synthetic data is not supported.
- **OOM (Out of Memory)**: Reduce `BATCH_SIZE` in `config.py` (e.g., from 32 to 8).
- **NaN in Embeddings**: Check audio files for corruption. Ensure `librosa` loads valid waveforms.
- **No Jailbreak Samples in Test Set**: Ensure `stratify=y` is used in `train_test_split`.
- **Slow Inference**: The pipeline is designed for CPU. Do not attempt to force GPU.

## Data Hygiene Note

- **Raw Data**: Never modify files in `data/raw/`.
- **Derived Data**: All derived files (embeddings, predictions) are written to `data/processed/` with timestamps.
- **Reproducibility**: Always run with the same `SEED` and `config.py` to reproduce results.
