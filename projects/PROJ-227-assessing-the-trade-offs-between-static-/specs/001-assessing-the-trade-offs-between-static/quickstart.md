# Quickstart: Assessing the Trade-offs Between Static and Dynamic Analysis for LLM-Generated Code

## Prerequisites

- Python 3.11+
- GitHub CLI (optional, for dataset access)
- CodeQL CLI (installed via `codeql` package or binary)
- SonarQube Scanner (installed via `sonar-scanner` package or binary)
- `pytest` for dynamic analysis

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-227-assessing-the-trade-offs-between-static-/
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install external tools** (if not pre-installed):
   - **CodeQL**: Download from https://github.com/github/codeql-cli-binaries
   - **SonarQube Scanner**: Download from https://www.sonarqube.org/downloads/

## Data Ingestion

1. **Run the download script**:
   ```bash
   python code/download.py
   ```
   - This will fetch datasets from verified HuggingFace URLs (HumanEval, HumanEval-X, CodeXGLUE, TheStack).
   - Checksums will be recorded in `data/raw/checksums.txt`.

2. **Verify data integrity**:
   ```bash
   python code/verify_data.py
   ```
   - Aborts if any file is corrupted.

## Running the Analysis

1. **Execute the full pipeline**:
   ```bash
   python code/main.py
   ```
   - This will:
     - Download and verify data.
     - Run static analysis (CodeQL, SonarQube, fallbacks) on all snippets.
     - Run dynamic analysis (unit tests) on snippets with oracles.
     - **Exclude `static_only` (BigCode) snippets from comparative tests**.
     - Aggregate results and run statistical tests (Spearman/Chi-squared).

2. **Monitor resource usage**:
   - The pipeline enforces CPU ≤ 2 cores and RAM ≤ 7 GB.
   - If limits are exceeded, the process will abort with an error code.

## Viewing Results

1. **Aggregated metrics**:
   ```bash
   cat data/processed/metrics.csv
   ```
   - Contains `detection_rate` (static) and `pass_rate` (dynamic).

2. **Statistical report**:
   ```bash
   cat data/processed/statistical_report.json
   ```
   - Contains correlation coefficients or Chi-squared p-values.

3. **Analysis logs**:
   ```bash
   head data/processed/analysis_logs.jsonl
   ```

## Troubleshooting

- **Static tool failures**: Check logs for `tool_failure` entries; fallback analyzers should have been attempted.
- **Timeouts**: Snippets marked as `timeout` are excluded from runtime metrics.
- **Resource limits**: If the pipeline aborts due to resource limits, reduce the sample size or optimize the analysis scripts.
- **Stratification Limitation**: If a language has <30 samples, it is excluded from stratified tests and reported as a limitation.

## Reproducibility

- All random seeds are pinned in `code/`.
- Datasets are fetched from canonical sources.
- Tool versions are logged in `state/projects/...yaml`.
- Re-run the pipeline on a fresh GitHub Actions runner to reproduce results.