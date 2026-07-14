# Quickstart: Developing New Methods to Synthesize High-Performance Membranes using Sustainable Materials

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM available (local or CI)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-022-developing-new-methods-to-synthesize-hig
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `rdkit`, `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `datasets`.*

4. **Verify RDKit installation**:
   ```bash
   python -c "import rdkit; print(rdkit.__version__)"
   ```

## Running the Pipeline

### 1. Data Ingestion & Standardization
Run the ingestion script to process literature data.
```bash
python code/ingestion/standardize_units.py --input data/raw/literature_raw.csv --output data/processed/standardized_polymers.csv
```
- *Expected Output*: `data/processed/standardized_polymers.csv`, `data/reports/missing_data_report.json` (if applicable), `data/reports/clarification_flag.json` (if 5-20% missing).

### 2. Feature Engineering
Calculate molecular descriptors and perform feature selection.
```bash
python code/features/calculate_descriptors.py --input data/processed/standardized_polymers.csv --output data/processed/feature_matrix.csv
```

### 3. Model Training & Validation
Train the Random Forest model with 5-fold CV.
```bash
python code/modeling/train_model.py --input data/processed/feature_matrix.csv --output artifacts/model.pkl --cv-results artifacts/cv_results.json
```
- *Expected Output*: `artifacts/model.pkl`, `artifacts/cv_results.json` (containing R², MAE).

### 4. Candidate Screening
Screen virtual candidates and run statistical tests.
```bash
python code/screening/rank_candidates.py --model artifacts/model.pkl --candidates data/raw/virtual_library.csv --output data/reports/screening_results.json
```
- *Expected Output*: `data/reports/screening_results.json` (Rankings, p-values).

### 5. Reporting
Generate final reports and candidate recommendations.
```bash
python code/screening/generate_report.py --results data/reports/screening_results.json --output data/reports/final_report.md
```
- *Expected Output*: `data/reports/final_report.md`, `data/reports/candidate_recommendation_report.md`.

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```
- **Contract Tests**: Verify schema compliance (e.g., `contracts/polymer_record.schema.yaml`).
- **Unit Tests**: Verify unit conversion, descriptor calculation.
- **Integration Tests**: Verify end-to-end pipeline execution.

## Troubleshooting

- **Runtime Error**: "Out of Memory" → Reduce `n_estimators` or `max_depth` in `train_model.py`.
- **Data Error**: "ERR_DATA_INSUFFICIENT" → Check `data/reports/missing_data_report.json`. Ensure at least 30 valid records exist.
- **Data Error**: "Held-Out Set Insufficient" → Check `data/reports/held_out_report.json`. Ensure at least 10 high-performance bio-membranes exist.
- **Import Error**: "RDKit not found" → Re-run `pip install rdkit-pypi`.

## Output Artifacts

- `data/processed/standardized_polymers.csv`: Cleaned dataset.
- `data/reports/clarification_flag.json`: Flag for low-to-moderate missing data.
- `artifacts/model.pkl`: Trained model.
- `data/reports/screening_results.json`: Final research output.
- `data/reports/power_analysis_report.json`: Statistical power analysis.
- `data/reports/candidate_recommendation_report.md`: Top candidates for future experimental validation.