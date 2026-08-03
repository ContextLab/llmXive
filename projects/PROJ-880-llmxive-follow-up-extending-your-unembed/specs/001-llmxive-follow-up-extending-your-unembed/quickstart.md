# Quickstart: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## 1. Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face Hub (for model weights)
- Internet connection (for dataset streaming)

## 2. Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-880-llmxive-follow-up-extending-your-unembed
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## 3. Data Acquisition

The pipeline is designed to fetch data on the fly. However, for local testing, you can pre-download the necessary models and datasets.

1. **Download Models** (via Hugging Face CLI):
   ```bash
   huggingface-cli download meta-llama/Meta-Llama-3-8B
   huggingface-cli download mistralai/Mistral-7B-v0.1
   huggingface-cli download bigscience/bloom-7b1
   ```

2. **Verify Data Sources**:
   Ensure you can access the RedPajama and Common Crawl datasets via `datasets`:
   ```python
   from datasets import load_dataset
   ds = load_dataset("togethercomputer/RedPajama-Data-1T", split="train", streaming=True)
   print(next(iter(ds)))
   ```

## 4. Running the Pipeline

### 4.1. Feasibility Check (T060)
Before running the full analysis, check if the SVD computation is feasible on your hardware.
```bash
python code/main.py --task check_feasibility
```
This will generate `data/processed/feasibility_report.json`.

### 4.2. Vocabulary Alignment Check (T065)
Check for vocabulary overlap between models.
```bash
python code/main.py --task check_vocab_alignment
```
This will generate `data/processed/vocab_alignment_warning.json`.

### 4.3. Full Analysis
Run the complete pipeline:
```bash
python code/main.py --task full_analysis
```
This will:
1. Load models one by one.
2. Extract edge spectrum subspaces.
3. Compute similarities.
4. Generate frequency distributions.
5. Run permutation tests.
6. Output `results/final_report.json`.

## 5. Expected Outputs

- `data/processed/similarity/cosine_matrix.json`: Cosine similarity scores between models.
- `data/processed/stats/permutation_results.json`: P-values and significance flags.
- `results/final_report.json`: Comprehensive summary of findings.

## 6. Troubleshooting

- **Memory Error**: If you encounter OOM errors, ensure you are using `streaming=True` for datasets and that models are unloaded after processing (`del model`, `torch.cuda.empty_cache()` if applicable, though this is CPU-only).
- **Model Loading**: If a model fails to load, check the Hugging Face token and network connectivity.
- **SVD Failure**: If `scipy.sparse.linalg.svds` fails, try increasing `k` or reducing the matrix size (not recommended for accuracy).
