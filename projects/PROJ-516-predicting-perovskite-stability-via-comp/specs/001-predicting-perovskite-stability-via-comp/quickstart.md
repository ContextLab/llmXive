# Quickstart: Predicting Perovskite Stability via Compositional Fingerprints

## Prerequisites

- Python 3.11+
- `pip`
- Access to the `data/` directory (raw data must be fetched or provided).
- `pymatgen` installed for formula parsing.

## Installation

1. **Clone and Setup Environment**:
   ```bash
   cd projects/PROJ-516-predicting-perovskite-stability-via-comp/code
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Verify Dependencies**:
   Ensure `scikit-learn`, `pandas`, `shap`, `requests`, `pyyaml`, `numpy`, and `pymatgen` are installed.

## Running the Pipeline

### 1. Data Ingestion
Fetch and process raw data. This step computes descriptors and filters for $T_d$.
```bash
python data_ingestion.py
```
*Output*: `../data/processed/descriptors.csv`

### 2. Model Training
Train baselines with cross-validation.
```bash
python model_training.py
```
*Output*: `../data/processed/model_runs.json`

### 3. Validation & Interpretability
Run SHAP analysis and external validation.
```bash
python validation.py
```
*Output*: `../data/processed/shap_analysis.json`, `../data/processed/external_metrics.json`

### 4. State Update
Update the project state file with artifact hashes.
```bash
python state_manager.py
```
*Output*: Updates `state/projects/PROJ-516-...yaml`

### 5. Full Pipeline
Run all steps sequentially.
```bash
python main.py
```

## Testing

Run the test suite to verify contract compliance and data integrity.
```bash
pytest tests/ -v --cov=code
```

## Troubleshooting

- **API Failures**: If `data_ingestion.py` fails to fetch NREL data, check network connectivity. The script includes automatic retry logic with a limited number of attempts and title-token-overlap validation.
- **Memory Errors**: If OOM occurs, reduce the dataset size in `model_training.py` (sample to a manageable subset) or increase swap space.
- **VIF Warnings**: If many features are flagged with VIF > 5, the pipeline will automatically drop the highest VIF feature or switch to Elastic Net.
- **Data Gap**: If NREL yields < 200 entries, the pipeline will halt with a "Data Gap" error. No secondary dataset is available.