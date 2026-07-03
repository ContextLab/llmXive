# Quickstart: Predicting the Glass Forming Region of Metallic Glass Alloys Using Machine Learning

## Prerequisites

- Python 3.11+
- Materials Project API key (set as `MP_API_KEY` environment variable)
- (Optional) Zenodo DOI for Metallic Glass dataset (if not using synthetic fallback)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Data Preparation

1. **Obtain Dataset**:
   - **Preferred**: The pipeline will automatically attempt to fetch data from the verified Zenodo DOI (configured in `config.yaml`).
   - **Fallback**: If the Zenodo fetch fails, the pipeline will generate a synthetic dataset automatically. No manual file upload is required.
   - **Manual Override**: You can provide a local CSV file by setting `--data-path` in the CLI, but this is not required for CI reproducibility.

2. **Set API Key**:
   ```bash
   export MP_API_KEY="your-materials-project-api-key"
   ```

3. **Run Data Ingestion**:
   ```bash
   python main.py --step ingest
   ```
   *Note: This step handles both Zenodo fetch and synthetic generation.*

## Running the Pipeline

```bash
# Full pipeline (ingest → features → train → evaluate)
python main.py

# Or run individual steps
python main.py --step features
python main.py --step train
python main.py --step evaluate
```

## Output Artifacts

- `data/processed/engineered_dataset.parquet` — Final dataset with descriptors
- `data/outputs/model_performance.csv` — Cross-validation metrics
- `data/outputs/shap_summary_rf.png` — SHAP plot for Random Forest
- `data/outputs/permutation_importance.csv` — Feature importance scores

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/
```

## Troubleshooting

- **"Zenodo fetch failed"**: The pipeline will automatically switch to synthetic data generation. No action required.
- **"Missing elemental properties"**: Rare elements may lack data in Materials Project; compositions with missing properties are dropped (logged).
- **"Out of memory"**: Reduce dataset size or increase swap space; pipeline is designed for ≤10,000 compositions.