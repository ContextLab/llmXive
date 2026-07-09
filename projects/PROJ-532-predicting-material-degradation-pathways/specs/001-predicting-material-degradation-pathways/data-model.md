# Data Model Specification

## Entities

### MaterialSample
- `id`: string (UUID)
- `composition`: map<string, float> (element -> weight %)
- `environment`: map<string, float> (pH, temp, etc.)
- `degradation_labels`: list<string> (pitting, SCC, etc.)

## Schemas
- Raw CSV: `data/raw/corrosion_data.csv`
- Cleaned CSV: `data/processed/cleaned_alloys.csv`
- Parquet: `data/processed/train_set.parquet`

## Constraints
- Composition must sum to ~100%
- Missing values < 5% per element (median imputation)
- Missing values >= 5% per element (drop record)
