# Quickstart: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

## Prerequisites

- Python 3.11+
- `bandit` (Python) and `cppcheck` (C) installed in the system path.
- Access to a GitHub Actions runner or local environment with ≥7GB RAM.

## Installation

1.  **Clone & Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-282-evaluating-the-effectiveness-of-llms-for
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    # requirements.txt includes: transformers, datasets, pandas, scikit-learn, tree-sitter, bandit, pydantic
    ```

3.  **Install System Tools**:
    ```bash
    # Ubuntu/Debian
    sudo apt-get update && sudo apt-get install -y cppcheck
    ```

## Running the Pipeline

### 1. Download Data
```bash
python src/main.py --stage download
```
*Downloads VulDeePecker, BigVul, and JS datasets to `data/raw/` and computes checksums.*

### 2. Preprocess & Sample
```bash
python src/main.py --stage preprocess
```
*Stratified sampling to a representative subset. Output: `data/processed/samples.csv`.*

### 3. Extract Features
```bash
python src/main.py --stage features
```
*Computes AST, complexity, and embeddings. Output: `data/processed/features.csv`.*

### 4. Run Inference (LLM + Static)
```bash
python src/main.py --stage inference
```
*Runs zero-shot LLM and static analyzers. Output: `data/processed/predictions_llm.csv`, `predictions_static.csv`.*

### 5. Analyze Results
```bash
python src/main.py --stage analysis
```
*Computes metrics, correlations, regression, and McNemar's test. Output: `data/processed/metrics.json`.*

## Verification

- **Check Sum**: `python src/utils/hash_artifacts.py --verify`
- **Run Tests**: `pytest tests/`

## Troubleshooting

- **OOM Error**: Reduce `BATCH_SIZE` in `src/config.py` to 1.
- **Missing Tool**: Ensure `cppcheck` is in `$PATH` for C analysis.
- **Timeout**: If runtime > 6h, the job will fail. Reduce sample size in `src/config.py`.
