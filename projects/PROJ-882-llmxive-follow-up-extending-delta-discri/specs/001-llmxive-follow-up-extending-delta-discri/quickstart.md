# Quickstart: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for dataset download)
- Sufficient disk space (for temporary model weights and data)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-882-llmxive-follow-up-extending-delta-descri
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
   *Note: `requirements.txt` pins `torch` to a CPU-only version and `sentence-transformers` for semantic similarity feature extraction.*

## Running the Pipeline

The entire pipeline can be executed end-to-end via the main script:

```bash
python code/main.py
```

This script performs the following steps automatically:
1. **Data Download**: Fetches GSM8K and filters for valid solutions (200 examples, seed=42).
2. **Oracle Generation**: Computes DelTA Coefficients using Phi-mini (~several hours).
3. **Feature Extraction**: Computes n-grams, POS, and semantic similarity using sentence-transformers/all-MiniLM-L6-v2.
4. **Training**: Trains the 2-layer MLP on CPU.
5. **Evaluation**: Computes Spearman correlation (example-level), permutation test, SHAP values, and collinearity analysis.

### Step-by-Step Execution (Debugging)

If you wish to run steps individually:

1. **Download & Filter**:
   ```bash
   python code/data/download_gsm8k.py
   ```

2. **Generate Oracle** (Phi-3-mini):
   ```bash
   python code/data/generate_oracle.py
   ```
   *Warning: This step is computationally intensive.*

3. **Extract Features** (sentence-transformers):
   ```bash
   python code/data/extract_features.py
   ```

4. **Train Model**:
   ```bash
   python code/models/train.py
   ```

5. **Evaluate** (example-level correlation, permutation test, SHAP, collinearity):
   ```bash
   python code/eval/metrics.py
   ```

## Expected Outputs

Upon successful completion, the `data/processed/` directory will contain:
- `delta_oracle.parquet`: Ground-truth coefficients (conforms to `contracts/delta_oracle.schema.yaml`).
- `features.parquet`: Input feature vectors (conforms to `contracts/static_features.schema.yaml`).
- `predictions.parquet`: Model predictions and metrics (conforms to `contracts/predictions.schema.yaml`).
- `example_level_aggregation.parquet`: Example-level aggregated predictions and targets.
- `feature_correlation_matrix.csv`: Pearson correlation matrix of input features (for collinearity analysis).
- `report.md`: A summary of the example-level Spearman correlation, p-value, feature importance (SHAP), and collinearity findings.

## Troubleshooting

- **Out of Memory (OOM)**: If the process crashes with OOM, check the memory estimates in `research.md` Section 5. Phi-mini requires a moderate amount of peak memory.; ensure your runner has sufficient RAM.
- **CUDA Error**: Ensure you are not accidentally importing `torch.cuda`. The code is designed for CPU only.
- **Oracle Generation Timeout**: If the Oracle generation exceeds a predefined time threshold, the pipeline fails explicitly with an error message. This is by design to ensure reproducibility. No partial-data fallbacks are used.
- **Feature Extraction Issues**: If semantic similarity computation fails, check that `sentence-transformers/all-MiniLM-L6-v2` is installed correctly and accessible.
