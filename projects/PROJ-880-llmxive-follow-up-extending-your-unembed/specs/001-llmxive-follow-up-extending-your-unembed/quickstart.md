# Quickstart: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## 1. Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to Hugging Face Hub (for model weights and datasets)
- Significant disk space (for streaming data)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-880-llmxive-follow-up-extending-your-unembed

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Data Acquisition

The pipeline automatically downloads required datasets. Ensure you have internet access.

```bash
# Run the data acquisition script
python code/utils.py --action download
```

This will:
- Download RedPajama (English) frequency data.
- Download Wikipedia (French, Chinese) frequency data.
- Download WALS features.
- Download SentEval benchmarks.

## 4. Running the Pipeline

Execute the main analysis pipeline:

```bash
python code/main.py --models llama3 mistral bloom --languages en fr zh
```

### Steps Performed:
1. **Load Models**: Load $W_U$ and $W_E$ for each model.
2. **SVD**: Compute a set of top singular vectors.
3. **Similarity**: Compute cosine similarity between subspaces.
4. **Token Attribution**: Identify top tokens in the edge spectrum.
5. **Validation**: Correlate shifts with WALS and SentEval.
6. **Permutation Test**: Compute p-values.

## 5. Output

Results are saved in `data/processed/`:

- `svd_results/`: SVD matrices.
- `subspace_metrics/`: Similarity matrices.
- `token_attribution/`: Top token lists.
- `validation_metrics/`: Correlation coefficients and p-values.
- `feasibility_report.json`: (If T060 is triggered).

## 6. Verification

Run the test suite to ensure correctness:

```bash
pytest tests/
```

Check the `data/processed/validation_metrics/validation_report.json` for the final p-value and correlation coefficients.
