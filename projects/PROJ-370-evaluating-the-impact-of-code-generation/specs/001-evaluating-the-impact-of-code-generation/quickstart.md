# Quickstart: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

## Prerequisites

- Python 3.11+
- Access to HuggingFace (free account required for dataset download)
- 2 CPU cores, 7GB+ RAM, 14GB+ disk space (standard GitHub Actions Free Tier)

## Installation

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `transformers`, `datasets`, `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `pytest`.*

## Running the Pipeline

The pipeline is executed via the CLI. It performs extraction, inference, alignment, and reporting in sequence.

### 1. Run Full Analysis
```bash
python -m src.cli.main --max-prs 500 --thresholds 0.80,0.85,0.90
```
- **`--max-prs`**: Limits the dataset size to fit memory (default 500).
- **`--thresholds`**: Specifies the sensitivity analysis thresholds.

### 2. Run Unit Tests
```bash
pytest tests/unit/
```
- Validates alignment logic and metric calculations.

### 3. Run Contract Tests
```bash
pytest tests/contract/
```
- Validates that all output files conform to the YAML schemas defined in `contracts/`.

### 4. Reproduce Results
To ensure reproducibility (Constitution Principle I), run with the same seed:
```bash
python -m src.cli.main --seed 42 --max-prs 500
```
*Random seeds are pinned in `src/config/settings.py`.*

## Output Artifacts

After a successful run, the following artifacts are generated:

- `data/derived/prs_cleaned.json`: Processed PR data.
- `data/derived/llm_bugs.json`: LLM bug detections.
- `data/derived/alignments.json`: Matched bugs.
- `results/final_report.json`: Comprehensive statistical report.
- `results/sensitivity_analysis.csv`: F1 scores across thresholds.

## Troubleshooting

- **Memory Error:** Reduce `--max-prs` or ensure no other heavy processes are running.
- **JSON Parse Error:** The system automatically retries up to 2 times. If it persists, the PR is skipped and logged.
- **Dataset Missing:** Ensure you have internet access to fetch from HuggingFace. The script checks for the presence of `data/raw/` before proceeding.
