# Quickstart: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## Prerequisites

- Python 3.10+
- Git
- Access to a terminal (local or GitHub Actions)

## Installation

1. **Clone the repository** (assuming you are in the project root):
   ```bash
   git checkout 001-predict-tg-metallic-glasses
   cd projects/PROJ-342-predicting-the-influence-of-alloying-on-/
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
   *Note: `requirements.txt` pins versions to ensure reproducibility (Constitution Principle I). This includes `mendeleev==0.31.0` for fixed periodic table data.*

## Data Setup

The pipeline expects raw data in `data/raw/`.
1. **Download Data**: Attempt to fetch from Zenodo DOI:
   - Primary: `10.5281/zenodo.10043838`
   - *Note: No fallback DOI is available. If this DOI is unreachable, the pipeline will halt.*
   *If automated download fails, manually place the CSV files in `data/raw/`.*
2. **Verify Checksums**:
   ```bash
   python code/ingest.py --verify-only
   ```

## Running the Pipeline

Execute the full pipeline (Ingest -> Train -> Analyze -> Report):

```bash
python code/ingest.py && \
python code/descriptors.py && \
python code/train.py && \
python code/analyze.py && \
python code/report.py
```

### Individual Steps
- **Ingest**: `python code/ingest.py` (Loads and cleans data; **enforces schema** from `../specs/001-predicting-the-influence-of-alloying-on/contracts/dataset.schema.yaml` using `jsonschema`).
- **Descriptors**: `python code/descriptors.py` (Computes atomic features).
- **Train**: `python code/train.py` (LOFO training + GridSearch).
- **Analyze**: `python code/analyze.py` (VIF, Bonferroni, Sensitivity; **enforces schema** from `../specs/001-predicting-the-influence-of-alloying-on/contracts/artifact.schema.yaml` using `jsonschema`).
- **Report**: `python code/report.py` (Generates `paper/report.md`).

## Testing

Run unit tests for descriptor logic:
```bash
pytest tests/unit/
```

Run integration tests (requires data presence):
```bash
pytest tests/integration/
```

## Expected Outputs

- `data/processed/descriptors.csv`: Cleaned data with features.
- `artifacts/models/best_model.pkl`: Trained model.
- `artifacts/metrics/stats.json`: Performance metrics and statistical tests.
- `paper/report.md`: Final scientific report.