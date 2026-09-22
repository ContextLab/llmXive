# Quickstart: Evaluating the Impact of Code Generation on Code Review Time

## Prerequisites

- Python 3.11+
- Git
- GitHub Personal Access Token (optional, for higher rate limits)
- Google Cloud SDK (for BigQuery access)
- Sufficient RAM, 14GB+ Disk

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-302-evaluating-the-impact-of-code-generation
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    Ensure `radon`, `transformers`, `torch`, `scikit-learn`, and `google-cloud-bigquery` are installed correctly.
    ```bash
    python -c "import radon, torch, sklearn, google.cloud.bigquery; print('Dependencies OK')"
    ```

## Running the Pipeline

### 1. Data Acquisition
Download and prepare the raw GitHub PR data (BigQuery + API).
**Note**: This step MUST retrieve the `diff` field from BigQuery.
```bash
python code/data_acquisition.py --stream --max-rows 500 --include-diffs
```
*Output*: `data/raw/github_prs.parquet`

### 2. Prompt Engineering
Extract intent from commit messages.
```bash
python code/prompt_engineering.py --input data/raw/github_prs.parquet
```
*Output*: `data/processed/intent_prompts.json`

### 3. Synthetic Code Generation
Generate LLM code snippets (Generation-from-Scratch and Refactoring).
*Note: This step will attempt CPU first. If it exceeds 60s, it will trigger the GPU escape hatch if configured.*
```bash
python code/synthetic_generation.py --cohort generation,refactoring --max-snippets 50
```
*Output*: `data/synthetic/llm_snippets.jsonl`

### 4. Feature Extraction
Calculate LOC, complexity, and semantic similarity (optional).
```bash
python code/feature_extraction.py --input data/raw/github_prs.parquet --synthetic data/synthetic/llm_snippets.jsonl
```
*Output*: `data/processed/features.parquet`

### 5. Propensity Score Matching & Analysis
Perform matching and statistical testing.
**Note**: This step excludes `semantic_similarity` from matching covariates.
```bash
python code/analysis.py --input data/processed/features.parquet --alpha 0.05
```
*Output*: `data/processed/matched_pairs.parquet`, `data/reports/statistical_results.json`, `data/reports/covariate_balance.json`, `data/reports/matching_failure_report.json` (if applicable)

### 6. Visualization
Generate box plots and CDF curves.
```bash
python code/visualization.py --input data/processed/matched_pairs.parquet --output data/reports/
```
*Output*: `data/reports/boxplot.png`, `data/reports/cdf.png`

### 7. Full Pipeline (End-to-End)
Run the entire workflow from scratch.
```bash
python code/main.py --full-run
```

## Verification

- **Check Covariate Balance**: Ensure `data/reports/covariate_balance.json` shows all SMD < 0.1.
- **Check Validity**: Ensure `data/reports/statistical_results.json` reports ≥95% syntactic validity for synthetic code.
- **Check Runtime**: Ensure `data/reports/runtime_report.json` shows total time ≤ 6 hours.
- **Check Reproducibility**: Re-run `main.py --full-run` and verify checksums match.

## Troubleshooting

- **Rate Limit Error**: Wait 60 seconds or provide a GitHub Token via `GITHUB_TOKEN` env var.
- **Memory Error**: Reduce `--max-rows` or `--max-snippets` in the respective commands.
- **Matching Failure**: If SMD > 0.1, the script will abort and generate `data/processed/matching_failure_report.json`. Adjust propensity parameters in `code/analysis.py` and retry.