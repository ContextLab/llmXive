"""
Script to generate quickstart.md and contracts/ schemas from the data model.
This task (T039) ensures documentation and schema artifacts are up-to-date.
"""
import os
from pathlib import Path
from code.models import Molecule, CrystalStructure, ModelResult

def generate_schema():
    """Generate the JSON/YAML schema for the dataset based on the data model."""
    schema_content = """%YAML 1.2
---
$schema: http://json-schema.org/draft-07/schema#
title: Molecular Crystal Packing Dataset Schema
description: >
  Schema for the processed dataset used in predicting molecular crystal packing
  from structural descriptors. Includes raw descriptors, imputed values, and
  stratified splits.
type: object
required:
  - metadata
  - columns
  - data
properties:
  metadata:
    type: object
    required:
      - version
      - created_at
      - source
      - checksum
    properties:
      version:
        type: string
        description: Schema version (e.g., "1.0.0")
      created_at:
        type: string
        format: date-time
        description: ISO 8601 timestamp of dataset creation
      source:
        type: string
        description: Source of the raw data (e.g., "Crystallography Open Database")
      checksum:
        type: string
        description: SHA-256 checksum of the raw source file
      split_strategy:
        type: string
        description: Method used for splitting (e.g., "stratified_by_mw")
  columns:
    type: array
    items:
      type: object
      required:
        - name
        - type
        - description
      properties:
        name:
          type: string
        type:
          type: string
          enum: [integer, float, string, boolean]
        description:
          type: string
        nullable:
          type: boolean
          default: false
        imputed:
          type: boolean
          default: false
          description: True if value was imputed
    minItems: 8
    description: >
      Expected columns: ID, Volume, SurfaceArea, Dipole, HBD, HBA, PSA, 
      packing_coefficient, mw, dipole_imputed, interaction_type, interaction_confidence
  data:
    type: array
    items:
      type: object
      required:
        - ID
        - packing_coefficient
      properties:
        ID:
          type: string
          description: Unique identifier from COD
        Volume:
          type: number
          minimum: 0
          description: Molecular volume in Å³
        SurfaceArea:
          type: number
          minimum: 0
          description: Molecular surface area in Å²
        Dipole:
          type: number
          nullable: true
          description: Dipole moment in Debye
        HBD:
          type: integer
          minimum: 0
          description: Number of hydrogen bond donors
        HBA:
          type: integer
          minimum: 0
          description: Number of hydrogen bond acceptors
        PSA:
          type: number
          minimum: 0
          description: Polar surface area in Å²
        packing_coefficient:
          type: number
          minimum: 0
          maximum: 1
          description: Ratio of molecular volume to unit cell volume
        mw:
          type: number
          minimum: 0
          description: Molecular weight in Da
        dipole_imputed:
          type: boolean
          description: Flag indicating if Dipole was imputed
        interaction_type:
          type: ["string", "null"]
          description: Dominant intermolecular interaction type
        interaction_confidence:
          type: ["number", "null"]
          minimum: 0
          maximum: 1
          description: Confidence score for interaction classification
examples:
  - metadata:
      version: "1.0.0"
      created_at: "2023-10-27T10:00:00Z"
      source: "Crystallography Open Database"
      checksum: "abc123..."
      split_strategy: "stratified_by_mw"
    columns:
      - name: ID
        type: string
        description: "Unique identifier"
      - name: packing_coefficient
        type: float
        description: "Target variable"
    data:
      - ID: "COD-12345"
        Volume: 120.5
        SurfaceArea: 250.0
        Dipole: 1.5
        HBD: 1
        HBA: 2
        PSA: 40.0
        packing_coefficient: 0.65
        mw: 180.16
        dipole_imputed: false
        interaction_type: "hydrogen_bond"
        interaction_confidence: 0.92
"""
    return schema_content

def generate_quickstart():
    """Generate the quickstart.md documentation."""
    quickstart_content = """# Quickstart Guide: Predicting Molecular Crystal Packing

This guide provides a step-by-step walkthrough to run the full pipeline for
predicting molecular crystal packing from structural descriptors using the
Crystallography Open Database (COD).

## Prerequisites

- Python 3.11+
- pip
- Git

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd PROJ-238-predicting-molecular-crystal-packing-fro
pip install -r requirements.txt
```

Ensure the following environment variables are set (optional, defaults provided):

```bash
export COD_URL="https://www.crystallography.net/cod-2023-09-01.tar.gz"
export RANDOM_SEED=42
export DATA_PATH="./data"
```

## 2. Ingest Data and Compute Descriptors

Download CIFs from COD, parse unit cell parameters, add missing hydrogens,
and compute molecular descriptors.

```bash
python code/01_ingest_and_descriptors.py
```

**Outputs:**
- `data/descriptors/raw_descriptors.csv`: Raw descriptor values.
- `data/processed/hydrogen_addition.log`: Log of hydrogen additions.

## 3. Impute and Filter Data

Handle missing values and filter physically impossible packing coefficients.

```bash
python code/02_impute_and_filter.py
```

**Outputs:**
- `data/processed/train.csv`, `val.csv`, `test.csv`: Stratified splits.
- `data/processed/filter_log.txt`: Exclusion log.

## 4. Train Models

Train Random Forest, Gradient Boosting, and Mean Predictor baseline models.

```bash
python code/02_train_models.py
```

**Outputs:**
- `results/models/`: Saved model artifacts.
- `results/metrics.json`: Initial performance metrics.

## 5. Evaluate and Report

Perform statistical evaluation, feature importance analysis, and sensitivity testing.

```bash
python code/03_evaluate_and_report.py
```

**Outputs:**
- `results/feature_importance.png`: Visualization of top features.
- `results/sensitivity_report.md`: LOFO analysis results.
- `results/interaction_classification.md`: Interaction type accuracy.

## 6. Verify Results

Validate the integrity of the output artifacts.

```bash
python code/verify_metrics.py
```

## Schema Reference

The dataset schema is defined in `contracts/dataset.schema.yaml`.
It specifies the required columns, data types, and metadata for all
processed datasets (raw, imputed, and split).

## Troubleshooting

- **Missing COD URL**: Ensure `COD_URL` is set or update `code/config.py`.
- **RDKit Errors**: Verify RDKit installation and version compatibility.
- **Memory Issues**: For large datasets, ensure sufficient RAM or use streaming.

## Next Steps

- Review `results/metrics.json` for model performance.
- Analyze `results/feature_importance.png` for descriptor insights.
- Read `results/sensitivity_report.md` for model robustness details.
"""
    return quickstart_content

def main():
    """Main entry point to generate artifacts."""
    # Ensure contracts directory exists
    contracts_dir = Path("contracts")
    contracts_dir.mkdir(exist_ok=True)

    # Write schema
    schema_path = contracts_dir / "dataset.schema.yaml"
    with open(schema_path, "w") as f:
        f.write(generate_schema())
    print(f"Generated schema: {schema_path}")

    # Write quickstart
    quickstart_path = Path("quickstart.md")
    with open(quickstart_path, "w") as f:
        f.write(generate_quickstart())
    print(f"Generated quickstart: {quickstart_path}")

if __name__ == "__main__":
    main()