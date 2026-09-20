"""
Script to generate quickstart.md and contract schemas from the data model.
"""
import os
import json
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import fields, is_dataclass

# Import the data model classes
from code.models import Molecule, CrystalStructure, ModelResult

def get_type_name(field_type: type) -> str:
    """Convert a Python type to a JSON schema type string."""
    if field_type is int:
        return "integer"
    elif field_type is float:
        return "number"
    elif field_type is str:
        return "string"
    elif field_type is bool:
        return "boolean"
    elif field_type is list:
        return "array"
    elif field_type is dict:
        return "object"
    else:
        return "string"  # Default fallback

def generate_schema_for_class(cls: type, schema_name: str) -> Dict[str, Any]:
    """Generate a JSON schema for a dataclass."""
    if not is_dataclass(cls):
        raise ValueError(f"{cls.__name__} is not a dataclass")

    properties = {}
    required = []

    for f in fields(cls):
        prop_name = f.name
        prop_type = get_type_name(f.type)
        
        # Handle optional types (simplified for common cases)
        if hasattr(f.type, '__origin__'):
            if f.type.__origin__ is Optional:
                prop_type = get_type_name(f.type.__args__[0])
                # Optional fields are not required
            elif f.type.__origin__ is list:
                prop_type = "array"
                # Add items type if possible
                if hasattr(f.type, '__args__') and f.type.__args__:
                    items_type = get_type_name(f.type.__args__[0])
                    properties[prop_name] = {
                        "type": "array",
                        "items": {"type": items_type}
                    }
                    required.append(prop_name)
                    continue
            elif f.type.__origin__ is dict:
                prop_type = "object"
                required.append(prop_name)
                continue
        else:
            required.append(prop_name)

        properties[prop_name] = {"type": prop_type}

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": schema_name,
        "type": "object",
        "properties": properties,
        "required": required
    }

    return schema

def generate_schemas(output_dir: Path) -> None:
    """Generate JSON schema files for all data model classes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    classes = [
        (Molecule, "molecule_schema.json"),
        (CrystalStructure, "crystal_structure_schema.json"),
        (ModelResult, "model_result_schema.json")
    ]

    for cls, filename in classes:
        schema = generate_schema_for_class(cls, cls.__name__)
        schema_path = output_dir / filename
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)
        print(f"Generated schema: {schema_path}")

def generate_quickstart(output_path: Path) -> None:
    """Generate a quickstart.md file."""
    content = """# Quickstart Guide: Predicting Molecular Crystal Packing

## Overview
This project predicts molecular crystal packing coefficients from structural descriptors using machine learning.

## Prerequisites
- Python 3.11+
- pip
- Access to the Crystallography Open Database (COD)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <project-dir>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables (optional):
   ```bash
   export COD_URL="https://www.crystallography.net/cod/cif/2/10/15/2101536.cif"
   export RANDOM_SEED=42
   export DATA_PATH="./data"
   ```

## Data Pipeline

### Step 1: Ingest and Compute Descriptors
Run the ingestion script to download CIF files and compute molecular descriptors:
```bash
python code/01_ingest_and_descriptors.py
```
This generates:
- `data/raw/cod_sample_ids.txt`: List of COD entry IDs
- `data/descriptors/raw_descriptors.csv`: Computed descriptors

### Step 2: Filter and Impute
Filter invalid packing coefficients and impute missing values:
```bash
python code/02_filter_packing_coefficient.py
python code/02_impute_and_filter.py
```
This generates:
- `data/processed/train.csv`, `val.csv`, `test.csv`: Split datasets

### Step 3: Train Models
Train Random Forest and Gradient Boosting models:
```bash
python code/02_train_models.py
```
This generates:
- `results/metrics.json`: Model performance metrics
- `results/control_analysis_metrics.json`: Control analysis results

### Step 4: Evaluate and Report
Perform feature importance analysis and generate reports:
```bash
python code/03_evaluate_and_report.py
python code/03_lofo_sensitivity.py
python code/03_control_analysis.py
```
This generates:
- `results/feature_importance.png`: Visualization of feature importance
- `results/sensitivity_report.md`: Sensitivity analysis results
- `data/interactions/interaction_classification.csv`: Interaction type classifications

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| `data/raw/cod_sample_ids.txt` | List of COD entry IDs |
| `data/descriptors/raw_descriptors.csv` | Raw molecular descriptors |
| `data/processed/train.csv` | Training dataset |
| `data/processed/val.csv` | Validation dataset |
| `data/processed/test.csv` | Test dataset |
| `results/metrics.json` | Model performance metrics |
| `results/feature_importance.png` | Feature importance plot |
| `results/sensitivity_report.md` | Sensitivity analysis report |

## Validation

To verify the pipeline:
```bash
python code/04_generate_quickstart.py
python code/verify_metrics.py
```

## Troubleshooting

- **Missing dependencies**: Ensure all packages in `requirements.txt` are installed.
- **COD access issues**: Check network connectivity and the `COD_URL` environment variable.
- **Memory errors**: Reduce the sample size in the ingestion script if running on limited hardware.

## License
This project is licensed under the terms specified in the repository.
"""
    
    with open(output_path, 'w') as f:
        f.write(content)
    print(f"Generated quickstart: {output_path}")

def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    
    # Generate schemas
    contracts_dir = project_root / "contracts"
    generate_schemas(contracts_dir)
    
    # Generate quickstart
    quickstart_path = project_root / "quickstart.md"
    generate_quickstart(quickstart_path)
    
    print("Quickstart and schemas generation complete.")

if __name__ == "__main__":
    main()