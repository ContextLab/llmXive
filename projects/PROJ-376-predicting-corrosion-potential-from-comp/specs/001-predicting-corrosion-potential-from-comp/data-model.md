# Data Model: Predicting Corrosion Potential from Composition and Environment

## Overview
Defines the schemas, entities, and transformations that underpin the corrosion‑potential prediction pipeline. All data artifacts must conform to the JSON‑Schema contracts in `contracts/`.

## Entity Definitions

| Entity | Key Fields | Description |
|--------|------------|-------------|
| **AlloyRecord** | `specific_alloy_designation` (str), `composition` (dict of element → weight fraction) | Represents one alloy grade. Weight fractions must sum to 1.0 (± 1e‑4). |
| **EnvironmentRecord** | `ph` (float 0‑14), `temperature_celsius` (float), `electrolyte_type` (categorical) | Testing conditions. |
| **CorrosionMeasurement** | `corrosion_potential_mV` (float), `measurement_method` (str) | Target variable linked to an alloy and environment. |
| **ModelResult** | `model_type`, `hyperparameters`, `metrics`, `feature_importance` | Output of training & evaluation. Conforms to `model_results.schema.yaml`. |

## Data Flow & Transformations
1. **Ingestion (`download_nist.py`)** → raw JSON/CSV → stored in `data/raw/`.  
2. **Schema Validation (`validate_schema.py`)** → checks non‑null fields, pH range, weight‑fraction sum, record count ≥ 500, ≥ 10 alloys. Fails with `SchemaMismatchError`.  
3. **Preprocessing (`preprocess.py`)**  
   - Drop rows missing `ph`, `temperature_celsius`, or `corrosion_potential_mV`.  
   - Flag pH < 0 or > 14 → `extreme_conditions.csv` (FR‑016).  
   - CLR transform all elemental weight fractions (FR‑020).  
   - One‑hot encode `electrolyte_type`.  
   - Perform **Group Split** by `specific_alloy_designation` with environment balancing (methodology‑0d5d2d9c).  
   - Output `clean_dataset.parquet` (train & test) under `data/processed/`.  

## Feature‑Importance Methodology
- **Conditional Permutation Importance (CPI)** is employed to respect the linear dependencies introduced by CLR transformation (addresses scientific_soundness‑0cb4417e).  
- Significance assessed via 1,000 permutations with Bonferroni/FDR correction (FR‑008).  

## Interpretability Visualisation
- **Accumulated Local Effects (ALE)** plots replace traditional PDPs for compositional features, mitigating the sum‑to‑zero constraint (addresses scientific_soundness‑9de34d4e).  

## File Formats
- **Raw**: Original CSV/JSON (unchanged).  
- **Processed**: Parquet (efficient columnar storage).  
- **Logs**: JSONL for structured pipeline logs.  
- **Schemas**: YAML files in `contracts/`.

## Assumptions & Constraints
- **Composition**: Provided as weight fractions; if not summing to 1, a normalization step is applied and logged.  
- **pH Scale**: Standard aqueous (acidic‑to‑basic). Non‑aqueous entries are flagged as outliers.  
- **Corrosion Potential**: Assumed vs SHE; any other reference is flagged.  
- **Observational Data**: Findings are associational only (Principle II).  

---

