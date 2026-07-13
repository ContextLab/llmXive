# Quickstart: llmXive Follow-up: Extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## 1. Prerequisites

*   **Python**: 3.11+
*   **System**: Linux (GitHub Actions runner or local Linux machine).
*   **RAM**: Minimum 8 GB (recommended 16 GB for safety, but 7 GB is the target limit).
*   **Disk**: ~20 GB free space (for model weights and data).
*   **Hugging Face Token**: Required to access Llama-3 and Qwen models. Set `HF_TOKEN` environment variable.

## 2. Installation

```bash
# Clone the project
git clone <repo-url>
cd projects/PROJ-880-llmxive-follow-up-extending-your-unembed

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Configuration

Create a `.env` file in the project root:

```bash
HF_TOKEN=your_huggingface_token_here
RANDOM_SEED=42
K_COMPONENTS=50
PERMUTATION_SWEEPS=10000
```

## 4. Running the Pipeline

The pipeline is executed in phases. You can run the full pipeline or individual steps.

### Full Pipeline (Recommended)

```bash
python code/run_pipeline.py
```

This will:
1.  Download and verify frequency lists.
2.  Extract edge spectra for Llama-3, BLOOM, and Qwen.
3.  Compute average token vectors.
4.  Perform Procrustes alignment.
5.  Run permutation tests and generate the final report.

### Individual Steps

**Step 1: Data Ingestion**
```bash
python code/data_ingestion.py
```

**Step 2: SVD Extraction**
```bash
python code/svd_extraction.py --model llama-3-8b
python code/svd_extraction.py --model bloom-7b1
python code/svd_extraction.py --model qwen1.5-7b
```

**Step 3: Alignment & Projection**
```bash
python code/alignment.py
python code/projection.py
```

**Step 4: Statistics**
```bash
python code/stats.py
```

## 5. Verifying Results

Check the `data/results/` directory for the final output files.
Run the validation script to ensure schema compliance:

```bash
python code/validate_results.py
```

## 6. Troubleshooting

*   **OOM Error**: If you get a MemoryError, ensure you are using `TruncatedSVD` and not `SVD`. Check that `safetensors` is being used.
*   **HF Token Error**: Ensure `HF_TOKEN` is set and the token has read access to the private models (if applicable).
*   **Missing Data**: If a frequency list is missing, the script will raise `DataMissingError`. Check the `data/raw/` directory.
