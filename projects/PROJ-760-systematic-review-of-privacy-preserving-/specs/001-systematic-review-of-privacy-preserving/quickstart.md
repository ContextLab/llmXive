# Quickstart: Systematic Review of Privacy-Preserving Federated Learning Protocols

## Prerequisites

- Python 3.11+
- Git
- GitHub account (for CI/CD)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

1. Execute the end-to-end pipeline:
   ```bash
   bash code/run.sh
   ```

2. The pipeline will:
   - Retrieve literature from arXiv and Semantic Scholar.
   - Extract metrics from PDFs.
   - Perform meta-regression and generate visualizations.
   - Output `results/results_summary.md` and `results/figures/`.

## Verifying Results

1. Check the log files for errors:
   ```bash
   cat code/review_needed.log
   cat code/parsing_errors.log
   ```

2. Validate the extracted dataset:
   ```bash
   python code/tests/integration/test_pipeline.py
   ```
   **Note**: This test verifies that `extracted_metrics.csv` contains REAL extracted values (non-zero, non-placeholder) and that all figures are generated from actual data, not simulated numbers.

3. Re-run on a fresh runner to verify reproducibility (SC-005).

## Troubleshooting

- **API Rate Limits**: The pipeline retries up to 3 times; check logs for persistent failures.
- **PDF Parsing Errors**: Non-standard tables are logged; manual review may be required.
- **Missing Metrics**: Studies lacking baseline for computational cost are excluded (FR-008).
- **Missing Variance**: If >50% of studies lack variance, the analysis falls back to descriptive statistics (median/IQR) rather than effect sizes.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request with tests and documentation updates.
