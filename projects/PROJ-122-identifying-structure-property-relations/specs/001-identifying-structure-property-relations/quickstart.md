# Quickstart: Identifying Structure-Property Relationships in Polymer Blends

## 1. Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution)
- **Verified dataset URL** for polymer blend data (SMILES, Composition, Tg, Modulus) — *Currently unavailable; see `research.md`*.

## 2. Installation

```bash
# Clone the repository
git clone
cd llmXive/projects/PROJ-122-identifying-structure-property-relations

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Setup

**Critical Note**: No verified dataset exists for the required polymer blend data. The pipeline will halt at the ingestion step if no valid source is provided.

To proceed, you must:
1. **Provide a verified URL** for a dataset containing SMILES, Composition, Tg, and Modulus for polymer blends.
2. **Update `config.py`** with the dataset URL.
3. **Run the ingestion script**:
 ```bash
 python src/01_ingest.py
 ```

If no verified URL is provided, the script will exit with:
```
ERROR: No verified source found for polymer blend data with SMILES, Composition, Tg, and Modulus.
```
The system will then attempt to switch to the **Monomer-Level Fallback** mode if monomer data is available.

## 4. Running the Pipeline

```bash
# Step 1: Ingest and harmonize data
python src/01_ingest.py

# Step 2: Sensitivity sweep (Weight-fraction tolerance)
python src/01b_sensitivity.py

# Step 3: Generate features (or fallback)
python src/02_features.py
# OR if fallback triggered:
python src/02b_fallback.py

# Step 4: Train models (Source Stratified Split)
python src/03_train.py

# Step 5: Evaluate and report
python src/04_evaluate.py
python src/05_metrics.py
python src/05_report.py
```

## 5. Verification

- **Contract Tests**: Run `pytest tests/contract/` to validate schemas.
- **Integration Tests**: Run `pytest tests/integration/` to test pipeline stages.
- **Unit Tests**: Run `pytest tests/unit/` to test utilities.
- **Rate Limit Test**: Run `pytest tests/integration/test_rate_limit.py` to verify SC-009.

## 6. Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `No verified source found` | Missing dataset URL | Provide a verified URL for polymer blend data. |
| `Data Insufficiency` | N < 100 | Collect more data or adjust spec. |
| `Memory Error` | Dataset too large | Enable stratified sampling (FR-017). |
| `VIF > 10` | High collinearity | Exclude predictor with highest VIF (FR-008). |
| `Runtime > 5 hours` | Too slow | Optimize code or sample data. |
| `Target Variable Missing` | Tg_measured not found | Skip residual calculation; report gap. |

## 7. Output

- `data/processed/final_report.json`: Contains MAE, R², p-values, feature importances, and stability metrics.
- `state/projects/PROJ-122-identifying-structure-property-relations.yaml`: Artifact hashes and versioning info.
- `logs/`: Execution logs for debugging.