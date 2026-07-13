# Quickstart: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## Prerequisites

- Python 3.11+
- Git
- ~Sufficient disk space (for model weights and datasets)
- Internet access (for HuggingFace downloads)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-880-llmxive-follow-up-extending-your-unembed
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: This installs CPU-only versions of `torch` and `transformers`.*

## Data Acquisition & Validation

The pipeline automatically downloads and validates datasets on first run. To manually verify:

```bash
python code/data_loader.py --download
```

This will:
1.  Fetch RedPajama subsets and OSCAR filters to `data/raw/`.
2.  **Validate** all URLs against the verified manifest.
3.  Generate checksums for all downloaded files.
4.  Generate checksums for all source files in `code/`.

## Running the Pipeline

Execute the full research pipeline:

```bash
python code/main.py
```

This script performs the following steps in order:
1.  **Validate & Download**: Fetches datasets and checks checksums. Fails if validation fails.
2.  **Model Loading**: Loads Llama-3, Mistral, and BLOOM $W_U$ matrices.
3.  **SVD Extraction**: Computes top-k singular vectors (with a fallback to a smaller k).
4.  **Token Projection**: Projects token embeddings onto the subspace.
5.  **Similarity & Attribution**: Computes cosine similarities and token rankings.
6.  **Bootstrap Test**: Runs multiple iterations using the Within-Language Baseline.
7.  **WALS Validation**: Computes correlation with external typological features.
8.  **Artifact Hashing**: Generates hashes for all `data/` and `code/` artifacts.
9.  **Report Generation**: Saves `similarity_report.json`, `permutation_result.json`, and `wals_validation.json` to `data/reports/`.

## Inspecting Results

- **Subspace Similarities**: `data/reports/similarity_report.json`
- **Token Attribution**: `data/reports/token_attribution.json`
- **Statistical Test**: `data/reports/permutation_result.json`
- **WALS Validation**: `data/reports/wals_validation.json`

To visualize the results (optional):
```bash
python code/visualize.py
```

## Troubleshooting

- **OOM Error**: If you encounter "Out of Memory", ensure no other GPU/CPU intensive processes are running. The script is designed for moderate RAM usage.; if you have less, reduce `k` in `code/config.py`.
- **Dataset Missing**: If the OSCAR filter fails, check your internet connection. The script will fall back to available subsets and log a warning.
- **Numerical Instability**: If SVD fails, the script will log the specific singular values and skip the problematic matrix, proceeding with others.
- **Validation Failure**: If `validate_sources()` fails, the pipeline will abort. Check the `data_loader.py` manifest for updated URLs.
