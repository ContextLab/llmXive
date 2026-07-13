# Quickstart: Evaluating the Impact of Code Generation on Code Review Time

## Prerequisites

- Python 3.11+
- GitHub API token (required for content fetching)
- Substantial disk space
- -hour runtime budget (GitHub Actions)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llm-code-review-impact/projects/PROJ-302-evaluating-the-impact-of-code-generation
 ```

2. **Create virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Set environment variables**:
 ```bash
 export GITHUB_TOKEN=your_token_here
 export RANDOM_SEED=42
 ```

## Running the Pipeline

### 1. Data Acquisition

```bash
python code/data_acquisition/github_scraper.py --repos "repo1,repo2" --output data/raw/pr_metadata.parquet
```

- Downloads PR metadata for specified repos.
- Implements exponential backoff for rate limits.
- Fetches raw file content for sampled PRs.

### 2. Style Classification

```bash
python code/data_acquisition/classifier_runner.py --input data/raw/pr_metadata.parquet --output data/processed/classified_snippets.parquet --model "codebert-base"
```

- Classifies code snippets as "LLM-like" or "Human-typical".
- Validates syntax and logs classifier params.

### 3. Feature Extraction

```bash
python code/feature_extraction/complexity.py --input data/processed/classified_snippets.parquet --output data/processed/features.parquet
python code/feature_extraction/timestamps.py --input data/processed/classified_snippets.parquet --output data/processed/features.parquet
```

- Computes LOC, complexity, review latency.

### 4. Propensity Score Matching

```bash
python code/analysis/matching.py --input data/processed/features.parquet --output data/processed/matched_pairs.parquet --covariates "file_size,complexity_score,repo_stars"
```

- Matches "Human-typical" and "LLM-like" pairs.
- Generates covariate balance report.
- **Note**: Semantic similarity is excluded from covariates.

### 5. Statistical Analysis

```bash
python code/analysis/statistical_test.py --input data/processed/matched_pairs.parquet --output data/processed/test_results.json
```

- Runs normality check (Shapiro-Wilk).
- Executes paired t-test or Mann-Whitney U.
- Outputs p-value and effect size.

### 6. Sensitivity Analysis & Visualization

```bash
python code/analysis/sensitivity.py --input data/processed/matched_pairs.parquet --output data/processed/sensitivity_results.json
python code/analysis/visualization.py --input data/processed/matched_pairs.parquet --output data/processed/visualizations/
```

- Stratifies by star quartiles.
- Generates box plots and CDF curves (bootstrapped).

### 7. Full Pipeline (Optional)

```bash
python code/main.py --config config.yaml
```

- Orchestrates all steps end-to-end.

## Validation

### 1. Contract Tests

```bash
pytest tests/contract/
```

- Validates data schemas against `contracts/`.

### 2. Integration Tests

```bash
pytest tests/integration/
```

- Runs pipeline on a small sample (a single repository, 100 PRs).

### 3. Unit Tests

```bash
pytest tests/unit/
```

- Tests individual functions (e.g., complexity calculation).

## Troubleshooting

### API Rate Limit Exceeded

- **Symptom**: `403 Forbidden` from GitHub API.
- **Fix**: Wait 1 hour or use a token with higher rate limits.

### Classification Fails

- **Symptom**: Low confidence scores.
- **Fix**: Exclude PRs with confidence < 0.7.

### Memory Error

- **Symptom**: `MemoryError` during feature extraction.
- **Fix**: Reduce sample size; process in smaller batches (1 PR at a time).

## Output Artifacts

- `data/raw/pr_metadata.parquet`: Raw GitHub API data.
- `data/processed/classified_snippets.parquet`: Classified code snippets.
- `data/processed/features.parquet`: Extracted features.
- `data/processed/matched_pairs.parquet`: Matched pairs.
- `data/processed/test_results.json`: Statistical test outputs.
- `data/processed/visualizations/`: Box plots, CDF curves.
- `data/checksums.yaml`: Artifact checksums.

## Next Steps

1. Review `plan.md` for detailed methodology.
2. Check `research.md` for dataset strategy and feasibility.
3. Run the pipeline and validate results against `contracts/`.
4. Generate the research paper using outputs from `data/processed/`.