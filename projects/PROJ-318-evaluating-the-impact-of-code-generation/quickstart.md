# Quickstart Guide: Evaluating the Impact of Code Generation Models

This guide provides step-by-step instructions to execute the full research pipeline for evaluating code generation models on code documentation completeness.

## Prerequisites

- Python 3.9+
- Git
- CUDA-compatible GPU (recommended for faster generation, CPU supported with 4-bit quantization)
- 16GB+ RAM (7GB minimum for strict monitoring)

## 1. Setup Environment

### Clone and Initialize Project
```bash
git clone <repository-url>
cd PROJ-318-evaluating-the-impact-of-code-generation
```

### Run Setup Script
Creates necessary directory structure and log files.
```bash
bash scripts/setup.sh
```

### Install Dependencies
```bash
pip install -r code/requirements.txt
```

## 2. Verify Configuration

Ensure the random seeds and constraints are correctly set in `code/config.py`.
```bash
python code/verify_seed.py
# Run twice to confirm reproducibility
python code/verify_seed.py
```

## 3. Data Extraction (User Story 1)

This phase extracts method signatures and human docstrings from top PyPI repositories.

### 3.1 Fetch Repository List
Generates a deterministic list of 20 top Python repositories.
```bash
python code/utils/repo_fetcher.py
```
*Output*: `data/raw/frozen_repo_list.json`

### 3.2 Clone Repositories
Clones the 20 repositories to `data/raw/repos/`.
```bash
python code/utils/git_clone.py
```

### 3.3 Extract Methods and Docstrings
Parses Python files and extracts signatures.
```bash
python code/extract.py
```
*Output*: `data/raw/repos/{repo_slug}.json` for each repository.

### 3.4 Verify and Hash Artifacts
Computes SHA-256 checksums and updates project state.
```bash
python code/serialize_and_hash.py
```

## 4. Docstring Generation (User Story 2)

Generates docstrings using the `Salesforce/codegen-350M-mono` model in 4-bit quantization.

### 4.1 Run Generation Pipeline
Processes all extracted methods with strict memory monitoring.
```bash
python code/generate.py
```
*Note*: The script enforces 4-bit quantization. If 4-bit fails, it aborts immediately.
*Output*: `data/processed/generation_batch_{repo_slug}.json`

### 4.2 Post-Process (Handle Empty Docstrings)
Flags records with empty or whitespace-only generated docstrings.
```bash
python code/post_process.py
```
*Output*: `data/processed/generation_batch_{repo_slug}_cleaned.json`

### 4.3 Aggregate Results
Merges all cleaned batch files into a single dataset.
```bash
python code/aggregate.py
```
*Output*: `data/processed/results.json`

## 5. Analysis (User Story 3)

Calculates coverage scores, semantic similarity, and statistical significance.

### 5.1 Calculate Parameter Coverage
Compares AST parameters against parsed docstring parameters.
```bash
python code/analyze.py --step=coverage
```
*Output*: `data/processed/results_with_coverage.json`

### 5.2 Calculate Semantic Similarity
Computes cosine similarity between human and generated docstrings.
```bash
python code/analyze.py --step=similarity
```
*Output*: `data/processed/results_with_scores.json`

### 5.3 Run Statistical Analysis
Performs Wilcoxon signed-rank test on coverage scores.
```bash
python code/analyze.py --step=stats
```
*Output*: `data/processed/results_with_stats.json`

### 5.4 Generate Final Report
Compiles all metrics and statistical results.
```bash
python code/analyze.py --report
```
*Output*: `data/processed/final_report.json`

## 6. Verification

### Reproducibility Check
```bash
bash scripts/verify_repro.sh
```
Ensures `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` matches the baseline hash.

## Troubleshooting

- **Memory Limit Exceeded**: The pipeline enforces a 7GB RAM limit. If `RAM_LIMIT_EXCEEDED` is logged, reduce batch size or use a machine with more RAM.
- **Quantization Failure**: If the model fails to load in 4-bit, the script will abort. Ensure `bitsandbytes` is correctly installed and compatible with your CUDA version.
- **Missing Dependencies**: Run `pip install -r code/requirements.txt` to ensure all libraries are installed.