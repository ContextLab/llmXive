# Quickstart: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

## Prerequisites
- Python 3.11+
- GitHub Personal Access Token (with `repo` scope)
- Sufficient disk space (for temporary git clones)
- GB RAM (minimum)

## Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```env
    GITHUB_TOKEN=your_token_here
    RANDOM_SEED=42
    ```

## Execution

### Step 1: Data Curation
Identify and clone repositories.
```bash
python code/01_curation.py
```
*Output*: `data/raw/repos.json`, cloned repos in `data/raw/clones/`.

### Step 2: Classification
Tag code blocks using CodeBERT.
```bash
python code/02_classification.py
```
*Output*: `data/processed/tagged_blocks.csv`.

### Step 3: Matching
Perform propensity score matching.
```bash
python code/03_matching.py
```
*Output*: `data/processed/matched_pairs.csv`.

### Step 4: Metrics Extraction
Extract churn and latency.
```bash
python code/04_metrics.py
```
*Output*: `data/processed/metrics.csv`.

### Step 5: Analysis & Visualization
Run statistical tests and generate plots.
```bash
python code/05_analysis.py
```
*Output*: `data/analysis/results.json`, `data/analysis/plots/`.

### Step 6: Ground Truth (Optional)
Select blocks for manual verification.
```bash
python code/06_ground_truth.py
```
*Output*: `data/ground_truth/labels.csv`.

## Validation

Run the test suite to verify data integrity and logic:
```bash
pytest tests/
```

## Troubleshooting

- **API Rate Limit**: If `403` errors occur, wait 1 hour or increase token permissions.
- **RAM Error**: Reduce `MAX_REPOS` in `code/utils/config.py` or process in smaller batches.
- **Model Load Error**: Ensure `onnxruntime` is installed and compatible with your CPU architecture.
