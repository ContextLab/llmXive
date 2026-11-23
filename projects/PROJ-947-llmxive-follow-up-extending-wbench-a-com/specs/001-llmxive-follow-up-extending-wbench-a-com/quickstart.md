# Quickstart: llmXive Follow-up: Extending WBench with Sequence Complexity Analysis

## 1. Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for dataset download)
- GitHub Actions Runner (Free Tier) or local environment with ≥7GB RAM.

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Data Download & Verification

```bash
# Run the download script
python code/data/download_wbench.py

# Verify checksums
python code/data/verify_checksums.py
```
*Expected Output*: `Checksums verified. Data ready in data/raw/`

## 4. Generating Sequence Variants

```bash
# Generate Low, Medium, High entropy variants with semantic plausibility check
python code/entropy/generator.py --input data/raw/first_person.parquet --output data/processed/variants.csv --min-similarity 0.85
```
*Expected Output*: `variants.csv` with columns `case_id`, `variant_type`, `semantic_similarity`, `complexity_score`.

## 5. Running Inference (CPU-Optimized or Proxy)

```bash
# Run inference on CPU models (or proxy metrics if no models fit)
# This will auto-skip models that exceed RAM limits or switch to proxy mode
python code/inference/runner.py --variants data/processed/variants.csv --output data/processed/inference_results.csv --subsample-size 50
```
*Expected Output*: `inference_results.csv` and video files (or proxy metric values) in `data/videos/`.

## 6. Statistical Analysis

```bash
# Run ANOVA and trend analysis (primary test)
python code/analysis/correlation.py --results data/processed/inference_results.csv --output results/analysis_summary.csv
```
*Expected Output*: `analysis_summary.csv` with F-statistics, p-values, and Bonferroni corrections.

## 7. Verification

To verify the pipeline:
```bash
pytest tests/
```
*Expected Output*: All tests pass, including `test_semantic_plausibility` and `test_cpu_inference`.

## 8. Troubleshooting

- **OOM Error**: If `inference/runner.py` fails with OOM, check RAM usage. The script should auto-skip the model or switch to proxy mode.
- **No Variance**: If `analysis/correlation.py` fails, check `variants.csv` to ensure `entropy_score` variance > 0.05.
- **Semantic Similarity Low**: If many variants are rejected, check the `--min-similarity` threshold (default 0.85) or the intent classifier model.
- **Dataset Missing**: Ensure HuggingFace token is set if required (though WBench is public).
