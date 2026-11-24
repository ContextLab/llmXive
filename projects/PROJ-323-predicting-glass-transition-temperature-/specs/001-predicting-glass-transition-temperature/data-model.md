# Data Model: Predicting Glass Transition Temperature from Compositional Descriptors with Explainable Boosting Machines

## Overview
The project manipulates three core data artifacts:

| Artifact | Description | Format | Primary Location |
|----------|-------------|--------|------------------|
| **Raw SMILES** | Collection of polymer SMILES strings (no $T_g$). | Parquet | `data/raw/smiles.parquet` |
| **Feature Matrix** | Engineered compositional descriptors (elemental fractions, functional-group counts, estimated MW). **No $T_g$ column is included**; the target column will appear only when a public $T_g$ dataset is added. | CSV | `data/processed/feature_matrix.csv` |
| **Physical Properties** | Fractional Free Volume (FFV) and Chain Stiffness values computed via Van Krevelen group contributions. | CSV | `data/physical_properties.csv` |
| **Model Output** | Serialized EBM model and associated metadata (hyperparameters, CV performance). | Pickle + JSON metadata | `outputs/models/ebm_model.pkl` + `outputs/models/ebm_metadata.json` |

All files are version-controlled, immutable, and accompanied by SHA-256 checksums recorded in `data/checksums.json`.

## Schema Definitions
- **Feature Matrix Schema** (`contracts/feature_matrix.schema.yaml`) – defines required columns, data types, and permissible value ranges (does **not** require a $T_g$ column).  
- **Model Output Schema** (`contracts/model_output.schema.yaml`) – validates that the serialized model contains expected attributes (`main_effects`, `interactions`, `hyperparameters`, `performance_metrics`).  

Both schemas are used by the CI test suite to guarantee data-contract compliance before any downstream analysis.

## Data Lineage
1. **Ingestion** reads the verified SMILES parquet → writes `data/raw/smiles.parquet` (checksum recorded).  
2. **Descriptor Engine** consumes `data/raw/smiles.parquet` → produces `data/processed/feature_matrix.csv` (new file; original untouched).  
3. **Physical Property Calculator** consumes `data/raw/smiles.parquet` → writes `data/physical_properties.csv`.  
4. **Model Trainer** (conditional) consumes `data/processed/feature_matrix.csv` (requires `experimental_tg` column; if absent, the stage is **skipped gracefully with a log message**) → writes `outputs/models/ebm_model.pkl` + metadata.  
5. **Interpretation & Validation** (conditional) consume the model and `data/physical_properties.csv` → generate figures & report.  

Each step logs its input checksum and output checksum, enabling reproducible reconstruction of any artifact.