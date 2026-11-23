# Quickstart: Evaluating the Effectiveness of LLMs for Detecting Code Smells

## Prerequisites
- Python 3.11+  
- Git  
- Access to the HuggingFace Hub (for dataset download)  

## 1. Setup Environment
```bash
# Clone the repository (if not already)
git clone https://github.com/your-org/your-repo.git
cd your-repo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2. Verify Dataset Availability
The pipeline requires a **verified** code dataset. The verification step checks that the dataset identifier appears in the project’s “# Verified datasets” block. The current verified dataset is:

- **Dataset**: `code-search-net/python` (Python subset of CodeSearchNet)  
- **URL**: `https://huggingface.co/datasets/code-search-net/python`

If this dataset is not listed in the verified block, the pipeline will abort with an informative error. To proceed:

1. Ensure the `DATASET_NAME` constant in `code/config.py` is set to `"code-search-net/python"`.  
2. Run the data pipeline (will abort if verification fails):

```bash
python code/data_pipeline.py --sample-size 800 --seed 42
```

*Expected output*: `data/processed/static_baseline.csv` with 800 rows.

## 3. Run Semantic Analysis
```bash
# Compute embeddings and run LLM inference (CPU‑only, batch size 10)
python code/semantic_analysis.py --batch-size 10 --model-path "CodeLlama-7B-Instruct-GGUF"
```

*Note*: The script will automatically download the MiniLM embedding model and the GGUF LLM if not cached locally.

## 4. Run Statistical Analysis
```bash
python code/statistical_analysis.py
```

*Expected output*:  
- `results/statistical_significance.json` (validated against `contracts/statistical_report.schema.yaml`)  
- `results/sensitivity_report.md`

## 5. Verify Results
```bash
# Run unit and contract tests
pytest tests/
```

All tests should pass, confirming that output files conform to the declared schemas.

## 6. Reproducibility Checklist
1. Use the same `--seed 42` for sampling.  
2. Use the exact `requirements.txt` versions.  
3. Record the dataset revision/tag in `code/config.py`.  
4. Verify checksums in `data/checksums.txt` after download.

Following these steps guarantees that anyone running the pipeline on a fresh GitHub Actions runner will obtain identical results.

---


