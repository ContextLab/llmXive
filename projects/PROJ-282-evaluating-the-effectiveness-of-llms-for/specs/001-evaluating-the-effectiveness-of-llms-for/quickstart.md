# Quickstart: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

## Prerequisites

- Python 3.11+
- Git
- `bandit` and `cppcheck` installed globally (or via Docker)
- Standard GitHub Actions runner with sufficient RAM and CPU cores to support the research question using the specified method (Citation: [DOI/arXiv/author-year]).

## Setup

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-282-evaluating-the-effectiveness-of-llms-for
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download Datasets**:
   Run the ingestion script to fetch and checksum data:
   ```bash
   python src/data/ingest.py --download
   ```
   *Note*: This will fetch VulDeePecker and JSVulnDB from Hugging Face. For NIST Juliet, it will `git clone` the official repository.

4. **Extract Features**:
   ```bash
   python src/data/feature_extractor.py --run
   ```
   This generates `data/processed/features.parquet` and logs `data/logs/stratification_verification.json` and `data/logs/dataset_substitution_justification.json`.

5. **Run Inference & Baselines**:
   ```bash
   python src/main.py --run-inference --run-baseline
   ```
   This executes LLM zero-shot inference and static analyzers, saving results to `data/results/predictions.csv`.

6. **Perform Statistical Analysis**:
   ```bash
   python src/models/regression.py --run-analysis
   ```
   This generates `data/results/analysis_metrics.csv` and plots.

## Verification

- Check `data/logs/stratification_verification.json` to ensure balanced sampling.
- Check `data/logs/dataset_substitution_justification.json` for dataset source changes.
- Verify `data/results/analysis_metrics.csv` contains non-null p-values and adjusted p-values.
- Run `pytest tests/` to ensure all unit and integration tests pass.

## Troubleshooting

- **Memory Error**: Reduce `--sample-size` in `ingest.py` or enable `--streaming`.
- **Parsing Error**: Check `data/logs/parse_errors.log` for malformed code snippets.
- **Timeout**: If runtime exceeds a predetermined threshold, the pipeline will automatically reduce the sample size.