# Quickstart: Evaluating the Effectiveness of LLMs for Detecting Code Smells

## Prerequisites
- Python 3.11+
- GB+ RAM (Free-tier CI compatible)
- Git
- Access to HuggingFace Hub (for dataset download)

## 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt** (Pinned versions for reproducibility):
```text
datasets==2.14.0
pandas==2.0.3
radon==6.0.1
pylint==3.0.1
sentence-transformers==2.2.2
llama-cpp-python==0.2.0
scikit-learn==1.3.0
statsmodels==0.14.0
numpy==1.24.0
pytest==7.4.0
```

## 2. Download & Verify Data

```bash
# Run the data pipeline to download and sample
python code/data_pipeline.py --sample-size --seed 42

# Verify checksums (if implemented)
python code/config.py --verify-checksums
```

*Expected Output*: `data/processed/static_baseline.csv` with 800 rows.

## 3. Run Semantic Analysis

```bash
# Run semantic embeddings and LLM inference (CPU only, batch size 10)
python code/semantic_analysis.py --batch-size 10 --model-path "CodeLlama-7B-Instruct-GGUF"
```

*Note*: Ensure `CodeLlama-7B-Instruct-GGUF` is available in the runner cache or download script.

## 4. Run Statistical Analysis

```bash
# Generate statistical report
python code/statistical_analysis.py
```

*Expected Output*: `results/statistical_significance.json` and `results/sensitivity_report.md`.

## 5. Verify Results

```bash
# Run unit and contract tests
pytest tests/
```

## 6. Reproducibility

To reproduce exactly:
1. Use the same `seed` in `data_pipeline.py`.
2. Ensure the same `requirements.txt` versions.
3. Use the same dataset version (HuggingFace `revision`).