# Quickstart: GraphCompass: Topological Predictors of Semantic Coherence in CPU-Constrained RAG

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution) or a local Linux environment with sufficient RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-911-llmxive-follow-up-extending-mcompassrag
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
    *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

## Data Preparation

The pipeline automatically downloads datasets on the first run. To manually verify:

1.  **Download HotpotQA**:
    ```bash
    python code/data_loader.py --dataset hotpot_qa --split fullwiki --output data/raw/hotpot_qa
    ```
2.  **Download Corpus (Wikipedia)**:
    ```bash
    python code/data_loader.py --dataset wikipedia --split 20231001.en --output data/raw/wikipedia
    ```

## Running the Pipeline

Execute the full research pipeline (Graph Construction -> Neural Baseline -> Retrieval -> Analysis):

```bash
python code/main.py
```

### Configuration
Edit `code/config.py` to adjust:
- `SAMPLE_SIZE`: Number of documents to process (default: a standard full rotation).
- `SLIDING_WINDOW`: Window size for graph construction (default: a representative sample size).
- `RANDOM_SEED`: Fixed seed for reproducibility (default: a representative value).
- `VOCAB_SIZE`: Size of fixed reference vocabulary for TF-IDF (default: a substantial number of samples).

## Verification

After the pipeline completes:

1.  **Check Output Files**:
    - `data/results/retrieval_metrics.json`: Contains Recall@5/10 scores and aggregated topological metrics.
    - `data/results/correlation_analysis.json`: Contains Spearman r and p-values.
2.  **Run Tests**:
    ```bash
    pytest tests/
    ```
    Tests include:
    - Unit tests for graph construction.
    - Contract tests validating output against `contracts/*.schema.yaml`.
    - Integration tests for the full pipeline on a small subset (N=10).

## Troubleshooting

- **Memory Error**: Reduce `SAMPLE_SIZE` in `config.py` or increase the sliding window size to reduce graph density.
- **CUDA Error**: Ensure `device="cpu"` is set in `code/neural_baseline.py`. Do not install `torch` with CUDA support.
- **Dataset Not Found**: Verify internet connection. The script uses `datasets.load_dataset` which requires network access.
- **Query Filtering**: If too few queries remain after filtering, check that the corpus version matches the HotpotQA version.