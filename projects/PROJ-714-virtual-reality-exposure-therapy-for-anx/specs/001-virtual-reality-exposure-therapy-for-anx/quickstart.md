# Quickstart: Virtual Reality Exposure Therapy Meta-Analysis

## Prerequisites

- Python 3.11+ installed.
- Git installed.
- (Optional) R installed (only if `metafor` integration is added later; currently Python-only).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-714-virtual-reality-exposure-therapy-for-anx
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Prepare Data
Place your raw CSV export of studies into `data/raw/studies.csv`.
*For testing, use the provided mock data:*
```bash
cp data/raw/mock_studies.csv data/raw/studies.csv
```

### 2. Execute the Analysis
Run the main pipeline script:
```bash
python code/main.py
```

This will:
1.  Load and validate `data/raw/studies.csv`.
2.  Apply inclusion criteria (FR-002).
3.  Compute Hedges' g for all included studies.
4.  Run the random-effects meta-analysis.
5.  Check for publication bias.
6.  Generate the PRISMA flow diagram, forest plot, and funnel plot.
7.  Compile `reports/final_report.pdf`.

### 3. Verify Results
- Check `data/processed/included_studies.csv` for the filtered list.
- Check `data/processed/meta_result.json` for the pooled statistics.
- Open `reports/final_report.pdf` to view the full synthesis.

### 4. Run Tests
To verify the math and pipeline logic:
```bash
pytest tests/
```

## Troubleshooting

- **"No studies included"**: Ensure your CSV has columns matching `contracts/study_schema.schema.yaml`. Check if all studies were excluded due to missing statistics.
- **"Egger's test not run"**: This is expected if $N < 10$. The report will state this limitation.
- **"ModuleNotFoundError"**: Ensure you activated the virtual environment and ran `pip install -r code/requirements.txt`.
