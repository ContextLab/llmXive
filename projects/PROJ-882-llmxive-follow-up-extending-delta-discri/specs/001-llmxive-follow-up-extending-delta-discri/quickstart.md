# Quickstart: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

## Prerequisites

- Python 3.11+
- Git
- HuggingFace CLI (optional, for model downloads)
- Kaggle CLI (optional, for GPU offload)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <project-dir>
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
   *Note: `requirements.txt` includes `datasets`, `transformers`, `torch`, `scikit-learn`, `sentence-transformers`, `pandas`, `pyarrow`, `spacy`.*

4. **Download language models** (optional, for offline use):
   ```bash
   python -m spacy download en_core_web_sm
   # Llama-3-1B and MiniLM will be downloaded automatically on first run
   ```

## Running the Pipeline

The pipeline is orchestrated by `code/main_pipeline.py`.

### Full Run (CPU + GPU Offload)

```bash
python code/main_pipeline.py
```

- **Step 1**: Downloads and filters GSM8K.
- **Step 2**: Computes DelTA coefficients (auto-offloads to Kaggle GPU if CPU fails).
- **Step 3**: Extracts static features.
- **Step 4**: Trains the Static MLP model.
- **Step 5**: Trains the Upper Bound Oracle model (Control).
- **Step 6**: Evaluates and saves metrics (including CI, Kendall's Tau, and classification).

### Individual Steps

**Download Data**:
```bash
python code/data/download_gsm8k.py
```

**Generate Oracle**:
```bash
python code/oracle/generate_oracle.py
```

**Generate Upper Bound**:
```bash
python code/oracle/generate_upper_bound.py
```

**Extract Features**:
```bash
python code/features/extract_features.py
```

**Train Model**:
```bash
python code/models/train.py
```

**Evaluate**:
```bash
python code/eval/metrics.py
```

## Expected Outputs

- `data/raw/gsm8k_verified.parquet`: Cleaned dataset.
- `data/processed/delta_coefficients.json`: Oracle ground truth (Flat format).
- `data/processed/upper_bound_predictions.json`: Upper Bound model predictions.
- `data/processed/static_features.parquet`: Feature vectors.
- `data/processed/mlp_model_static.pt`: Trained Static Model.
- `data/processed/mlp_model_upper.pt`: Trained Upper Bound Model.
- `data/processed/metrics.json`: Final results (includes classification, CI, and causal disclaimer).

## Troubleshooting

- **CUDA Out of Memory**: The pipeline will automatically retry on Kaggle GPU. Ensure `KAGGLE_USERNAME` and `KAGGLE_KEY` are set if running locally on Kaggle.
- **Variance Check Failed**: If `ERR_TRIVIAL_TARGET` is raised, the dataset subset may be too homogeneous. Try increasing the subset size or checking the filtering logic.
- **MiniLM Download Failed**: Ensure internet access or pre-download the model to `~/.cache/huggingface`.
- **Classification Logic**: If the result is "Emergent", it means the signal is not recoverable from static features but is recoverable from hidden states. If "Poor Proxies", the signal is not recoverable from either.
