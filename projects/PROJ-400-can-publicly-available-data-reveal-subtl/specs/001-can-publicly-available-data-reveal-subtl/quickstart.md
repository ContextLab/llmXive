# Quickstart: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for optional NNDC fetch; static data works offline)

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   cd projects/PROJ-400-can-publicly-available-data-reveal-subtl
   ```

2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```
   *Note: `scikit-learn` is NOT required. Dependencies are `requests`, `pandas`, `numpy`, `scipy`, `pyyaml`, `pytest`.*

## Running the Pipeline

### Full Execution
To run the complete data retrieval (static fallback + optional fetch), meta-analysis, and validation pipeline:
```bash
python code/main.py --nuclei "6He,19Ne"
```
- This command loads the **static fallback** data for 6He and 19Ne.
- It *attempts* to fetch updated data from NNDC (non-blocking).
- Results are saved to `data/derived/`.

### Running Specific Modules

#### 1. Data Retrieval Only (Static + Optional Fetch)
```bash
python code/data_retrieval.py --nuclei "6He,19Ne" --output data/derived/harmonized.csv
```

#### 2. Meta-Analysis Only
```bash
python code/meta_analysis.py --input data/derived/harmonized.csv --output data/derived/meta_results.csv
```

#### 3. Sign-Flip Permutation Testing (Null Hypothesis)
```bash
python code/permutation_test.py --input data/derived/harmonized.csv --shuffles 10000 --output data/derived/null_distribution.csv
```

#### 4. Validation Against PDG (Static Reference)
```bash
python code/validation.py --input data/derived/meta_results.csv --output data/derived/validation_results.csv
```
*Note: PDG data is loaded from a static reference (hardcoded in code), not an external URL.*

## Verifying Results

1. **Check Checksums**: Ensure data integrity by running:
   ```bash
   sha256sum data/derived/*
   ```
   Compare against `data/checksums.txt` (generated automatically).

2. **Review Output**: Open `paper/results.md` to see the generated report.
   - Verify the "Combined D-Coefficient" and "Upper Bound".
   - Check the "Consistency Test" p-value (should be > 0.05 for consistent data).
   - Confirm the "Validation" status against PDG.

3. **Run Tests**:
   ```bash
   pytest tests/
   ```
   - Unit tests verify statistical formulas (including Sign-Flip logic).
   - Integration tests verify the data pipeline (using the static fallback).

## Troubleshooting

- **NNDC Connection Error**: The script will log the error and proceed with the **static fallback** data. The pipeline will not fail.
- **Missing Data**: If a nucleus has no data (even in static fallback), it will be excluded from the meta-analysis. Check `data/derived/harmonized.csv` for the `retrieval_status` column.
- **PDG Data Load Error**: The PDG data is hardcoded. If the validation step fails, check the `code/validation.py` for the static reference values.