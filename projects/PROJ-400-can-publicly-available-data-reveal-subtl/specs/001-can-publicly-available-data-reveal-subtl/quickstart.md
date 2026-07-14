# Quickstart: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Access to GitHub Actions (for CI execution) or a local Linux environment.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-400-can-publicly-available-data-reveal-subtl
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
   *Note: `requirements.txt` will pin `requests`, `pandas`, `scipy`, `numpy`, `pyyaml`, `pytest`, `pdfplumber`.*

## Running the Pipeline

### 1. Data Retrieval (and Fallback)
The system attempts to fetch data from the PDG 2024 Review. If the network is unreachable or the PDF parsing fails, it logs an error and halts the scientific analysis (unless `--test-mode` is explicitly set for CI testing with mock data).

```bash
python code/main.py --mode retrieve
```
*Output*: `data/processed/harmonized_d_measurements.csv`

### 2. Meta-Analysis & Validation
Runs the statistical analysis (Z-test, inverse-variance weighting), consistency checks (Cochran's Q), and PDG 2022 comparison.

```bash
python code/main.py --mode analyze
```
*Output*: `data/processed/meta_analysis_results.csv`, `results/summary_report.md`

### 3. Consistency Check (Shuffle Fallback)
Explicitly runs the shuffle fallback for Cochran's Q if the analytic p-value is borderline and n < 5.

```bash
python code/main.py --mode shuffle --shuffles 10000
```

### 4. Testing
Run the unit and contract tests.

```bash
pytest tests/
```

## Expected Outputs

- **CSV Files**: Harmonized measurements and meta-analysis results.
- **Markdown Report**: A summary of the combined D-coefficient, Z-test result (discovery vs. limit), upper bound, and consistency p-value.
- **Logs**: Detailed logs of any skipped nuclei or API failures.

## Troubleshooting

- **API Timeout**: If the PDG API/PDF is down, the script will log a warning and proceed with mock data **ONLY** if `--test-mode` is set. Otherwise, it halts to prevent unverified scientific results.
- **Missing Nucleus**: If a requested nucleus (e.g., 6He) has no data, it is excluded from the analysis, and the report notes "insufficient data".
- **Circularity Avoidance**: The system compares against the 2022 PDG limit, not the 2024 limit, to ensure valid validation.