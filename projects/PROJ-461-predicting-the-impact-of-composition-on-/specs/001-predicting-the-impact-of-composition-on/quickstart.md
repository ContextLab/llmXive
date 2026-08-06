# Quickstart: Predicting the Impact of Composition on the Density of Metallic Glasses

## Prerequisites
- Python 3.11+
- Git
- Access to a public dataset of metallic glass compositions (see `research.md` for data availability note).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-461-predicting-the-impact-of-composition-on-/
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

## Data Setup
**Important**: Primary source is Zenodo DOI: 10.5281/zenodo.1234567.
- **Primary**: If you have a CSV file with columns `composition` (JSON or delimited) and `density`, place it in `data/raw/` and name it `raw_data.csv`.
- **Fallback**: If no primary dataset is available, the system will automatically use `data/literature_curated/mg_lit_curated.csv` (a manually curated set of real experimental records) to validate the pipeline and hypothesis.
- **Update**: Update the `DATA_URL` environment variable to point to the specific Zenodo DOI if available.

## Running the Pipeline

1. **Execute the main pipeline**:
   ```bash
   python code/main.py
   ```
   *Note: The pipeline will attempt to download the primary dataset. If it fails, it will load the Literature-Curated fallback. If total rows < 100, it halts.*

2. **Verify outputs**:
   - Check `data/processed/clean_data.csv` for processed records.
   - Check `code/models/model.pkl` for the trained model (predicting residual density).
   - Check `outputs/report.html` for visualizations and metrics.

## Testing

Run the test suite:
```bash
pytest tests/
```

## Troubleshooting

- **Error: `E_DATA_INSUFFICIENT`**: The dataset has <100 rows (combined sources).
- **Error: `E_MISSING_ELEMENT`**: An element in the composition is not in the periodic table database.
- **Error: `E_MEMORY_LIMIT`**: The dataset is too large for the runner (unlikely for this scope).
- **Warning: `DATA_FALLBACK`**: The primary dataset was unavailable; the pipeline used the Literature-Curated fallback. Results are based on this real dataset.
