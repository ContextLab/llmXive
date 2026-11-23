# Quickstart: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Prerequisites

- Python 3.11+
- Git
- (Optional) A CSV file of extracted studies (`data/raw/studies.csv`) for real analysis.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-082-investigating-the-correlation-between-st
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### Option A: Test with Mock Data (Recommended for CI/CD)

This generates a synthetic dataset and runs the full analysis to verify the pipeline.

```bash
# Generate mock data (creates data/raw/mock_studies.csv)
python code/data/generators.py --config default

# Run the full pipeline using mock data
python code/main.py --input data/raw/mock_studies.csv --output data/processed/meta_results.json
```

**Expected Output**:
- `data/processed/study_count.json` (N ≥ 10, mode: quantitative)
- `data/processed/meta_results.json` (Pooled r, I², Egger's test)
- `data/derived/plots/forest_plot.png`, `funnel_plot.png`

### Option B: Run with Real Data (Narrative Fallback)

If you have a real `studies.csv` with < 10 studies:

1.  Place your file at `data/raw/studies.csv`.
2.  Run the pipeline:
    ```bash
    python code/main.py --input data/raw/studies.csv --output data/processed/meta_results.json
    ```
3.  **Result**: The system will detect N < 10, skip quantitative analysis, and generate a `narrative_summary` in the output JSON.

### Option C: Run with Real Data (Quantitative)

If you have a real `studies.csv` with ≥ 10 studies:
1.  Ensure `studies.csv` is in `data/raw/`.
2.  Run the pipeline as in Option B.
3.  **Result**: Full meta-analysis, heterogeneity, and bias tests will be performed.

## Verification

Run the test suite to ensure all components work:

```bash
pytest tests/ -v
```

Key tests to pass:
- `test_extraction`: Verifies FR-001.
- `test_meta_analysis`: Verifies FR-002, FR-003, FR-005.
- `test_bonferroni`: Verifies SC-004.
- `test_narrative_fallback`: Verifies FR-006, SC-005.

## Troubleshooting

- **Error: "Insufficient studies"**: This is expected if N < 10. The system has correctly pivoted to narrative mode.
- **Error: "Convergence failed"**: The model will fallback to fixed-effects (if N ≥ 10) or narrative mode. Check logs in `data/derived/validation_report.json`.
- **Missing `studies.csv`**: Use `code/data/generators.py` to create mock data for testing.
