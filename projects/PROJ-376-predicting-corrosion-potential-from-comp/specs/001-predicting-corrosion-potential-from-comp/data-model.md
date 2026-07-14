# Data Model: Predicting Corrosion Potential from Composition and Environment

## 1. Entity Relationship Diagram (Conceptual)

The data model consists of three core entities linked by a unique `record_id`.

```mermaid
erDiagram
    AlloyRecord ||--o{ CorrosionMeasurement : "has"
    EnvironmentRecord ||--o{ CorrosionMeasurement : "defines"
    
    AlloyRecord {
        string specific_alloy_designation "e.g., SS304"
        float fe_weight_fraction
        float cr_weight_fraction
        float ni_weight_fraction
        float mo_weight_fraction
        // ... other elements
    }
    
    EnvironmentRecord {
        float ph
        float temperature_celsius
        string electrolyte_type "e.g., saline, acidic"
        string reference_electrode "e.g., SHE, SCE, Ag/AgCl"
    }
    
    CorrosionMeasurement {
        string record_id
        float corrosion_potential_mv
        string test_standard "e.g., ASTM G59"
    }
```

## 2. Schema Definitions

### 2.1 Raw Input Schema (NIST-IR-8200)
*Expected fields from the source.*
- `record_id`: Unique identifier.
- `alloy_name`: String (e.g., "Stainless Steel 304").
- `composition`: JSON object `{ "Fe": 0.70, "Cr": 0.18, ... }`.
- `environment`: JSON object `{ "pH": 7.0, "temp": 25.0, "type": "neutral", "reference": "SHE" }`.
- `corrosion_potential`: Float (mV).

### 2.2 Processed Dataset Schema (Parquet)
*The unified dataset used for training.*

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `record_id` | String | Unique identifier | Non-null, Unique |
| `specific_alloy_designation` | String | Normalized alloy grade (e.g., "SS304") | Non-null |
| `fe_weight` | Float64 | Iron weight fraction | 0.0 ≤ x ≤ 1.0 |
| `cr_weight` | Float64 | Chromium weight fraction | 0.0 ≤ x ≤ 1.0 |
| `ni_weight` | Float64 | Nickel weight fraction | 0.0 ≤ x ≤ 1.0 |
| `mo_weight` | Float64 | Molybdenum weight fraction | 0.0 ≤ x ≤ 1.0 |
| `other_elements` | Float64 | Sum of remaining elements | 0.0 ≤ x ≤ 1.0 |
| `ph` | Float64 | Environmental pH | 0.0 ≤ x ≤ 14.0 |
| `temperature_c` | Float64 | Temperature in Celsius | > 0 |
| `corrosion_potential_mv` | Float64 | Target variable (normalized to SHE) | Non-null |
| `reference_electrode` | String | Original reference electrode | Non-null (e.g., SHE, SCE) |
| `is_outlier` | Boolean | Flag for extreme pH | False (default) |

### 2.3 Split Strategy
- **Training Set**: All records where `specific_alloy_designation` is in the training group (GroupKFold).
- **Test Set**: All records where `specific_alloy_designation` is in the test group (GroupKFold).
- **Constraint**: Intersection of alloy designations between Train and Test must be **empty** within each fold.

## 3. Data Lineage

1. **Raw**: `data/raw/nist_corrosion.jsonl` (Downloaded from source).
2. **Cleaned**: `data/processed/cleaned_data.csv` (Filtered for non-null pH, temp, composition, reference electrode).
3. **Final**: `data/processed/corrosion_dataset.parquet` (Encoded, split-ready, potentials normalized to SHE).
4. **Logs**: `data/logs/pipeline.log` (Record of exclusions, errors, normalization steps).

## 4. Error Handling

- **SchemaMismatchError**: Raised if required columns (pH, temp, composition, reference electrode) are missing in the source.
- **DataInsufficientError**: Raised if total records < 500 or unique alloys < 10.
- **OutlierFlag**: Records with pH < 0 or pH > 14 are flagged but not removed from the raw log; they are excluded from the training set.
- **ReferenceMismatchError**: Raised if the reference electrode is missing or cannot be converted to SHE.