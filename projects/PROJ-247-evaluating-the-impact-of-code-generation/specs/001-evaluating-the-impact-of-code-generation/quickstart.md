# Quickstart: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

## Prerequisites
- Python 3.11+
- GitHub Personal Access Token (with `repo` scope)
- Sufficient disk space (for temporary git clones)
- Adequate RAM (minimum)

## Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Install Dependencies**
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env to add your GITHUB_TOKEN
   ```

## Execution

The pipeline is executed as a series of sequential scripts. Run them in the following order:

### Step 1: Data Curation
Identify and clone repositories.
```bash
python code/01_data_curation.py
```
*Output*: `data/raw/repo_list.csv`, `data/raw/repo_metadata.csv`, cloned repos in `data/raw/clones/`.

### Step 2: Classification
Tag code blocks using CodeBERT.
```bash
python code/02_classification.py
```
*Output*: `data/processed/tagged_blocks.csv`.

### Step 3: Matching
Perform propensity score matching.
```bash
python code/utils/matching.py
```
*Output*: `data/processed/matched_pairs_filtered.csv`.

### Step 4: Metrics Extraction
Extract churn and latency.
```bash
python code/02_metric_extraction.py
```
*Output*: `data/processed/metrics_longitudinal.csv`.

### Step 5: Analysis & Visualization
Run statistical tests and generate plots.
```bash
python code/03_analysis.py
python code/03_visualization.py
```
*Output*: `data/analysis/wilcoxon_results.json`, `figures/fig_churn_boxplot.png`, etc.

### Step 6: Ground Truth (Optional)
Select blocks for manual verification.
```bash
python code/04_ground_truth_selection.py
```
*Output*: `data/ground_truth/manual_labels.csv`.

## Validation

Run the test suite to verify data integrity and logic:
```bash
python -m pytest tests/
```

## Troubleshooting

- **API Rate Limit**: If `403` errors occur, wait 1 hour or increase token permissions.
- **Model Load Error**: Ensure internet connectivity; the script will download the ONNX model on first run.
- **RAM Error**: Reduce the number of processed repositories in the curation script.