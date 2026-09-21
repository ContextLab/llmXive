# Quickstart: Automated Detection of Algorithmic Bias in Public Code Repositories

## 1. Prerequisites

- Python 3.11+
- `pip`
- Git
- GitHub API Token (optional, for rate limit extension)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd <repo-path>

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt** includes:
```text
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
vaderSentiment>=3.3.2
fairlearn>=0.9.0
datasets>=2.14.0
pyyaml>=6.0
pytest>=7.0.0
```

## 3. Data Setup

1. **Download VADER Lexicon**:
   The pipeline automatically fetches the verified VADER dataset from HuggingFace on first run.
   ```python
   # Or manually to verify
   from datasets import load_dataset
   ds = load_dataset("bartoszmaj/vader_sentiment_full", split="train")
   ```

2. **Prepare Validation Set**:
   Place `comments.csv` in `data/validation/` with columns `comment`, `label` (0/1).

3. **Prepare Test Repos**:
   Place a list of GitHub URLs in `data/raw/repo_list.txt` (one per line).

## 4. Running the Pipeline

```bash
# Run the full pipeline
python -m src.cli.main --repos data/raw/repo_list.txt --output data/processed/

# Run validation only
python -m src.cli.main --validate --validation-data data/validation/comments.csv

# Run simulation only
python -m src.cli.main --simulate --skew-magnitude 0.1
```

## 5. Output Interpretation

- **`data/processed/bias_scores.jsonl`**: Per-repo textual bias metrics.
- **`data/processed/fairness_metrics.jsonl`**: Per-repo simulated fairness metrics.
- **`data/processed/correlation_results.csv`**: Final statistical results (Spearman, p-values).
- **`state/projects/...yaml`**: Checksums and execution status.

## 6. Troubleshooting

- **Rate Limit**: If GitHub API fails, increase token scope or reduce repo count.
- **Memory Error**: Reduce `--max-repos` or enable streaming (default).
- **Syntax Error**: Handled automatically; repo marked as "error" in logs.
