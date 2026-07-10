"""
Setup script for creating data directories and validating schema.
This script ensures the required directory structure exists and
the output schema is correctly defined.
"""
import os
import yaml
from pathlib import Path

def main():
    # Define project root relative to this script location
    # Assuming script is in code/ directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    output_dir = data_dir / "output"
    
    # Create directories
    directories = [
        data_dir,
        raw_dir,
        processed_dir,
        output_dir
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified directory: {directory}")
    
    # Define schema content based on task requirements
    schema_content = {
        "version": "1.0",
        "description": "Schema for the merged dataset containing molecular descriptors and degradation data.",
        "fields": [
            {
                "name": "SMILES",
                "type": "string",
                "required": True,
                "description": "Canonical SMILES string of the molecule."
            },
            {
                "name": "half_life_hours",
                "type": "float",
                "required": True,
                "description": "Degradation half-life in hours."
            },
            {
                "name": "tPSA",
                "type": "float",
                "required": True,
                "description": "Topological Polar Surface Area."
            },
            {
                "name": "rotatable_bonds",
                "type": "integer",
                "required": True,
                "description": "Count of rotatable bonds."
            },
            {
                "name": "molecular_weight",
                "type": "float",
                "required": True,
                "description": "Molecular weight (MW)."
            },
            {
                "name": "aromatic_rings",
                "type": "integer",
                "required": True,
                "description": "Count of aromatic rings."
            },
            {
                "name": "wiener_index",
                "type": "float",
                "required": True,
                "description": "Wiener index (topological index)."
            },
            {
                "name": "zagreb_index",
                "type": "float",
                "required": True,
                "description": "Zagreb index (topological index)."
            },
            {
                "name": "drug_name",
                "type": "string",
                "required": False,
                "description": "Name of the drug (if available in source)."
            }
        ],
        "constraints": {
            "no_nulls": [
                "SMILES",
                "half_life_hours",
                "tPSA",
                "molecular_weight"
            ],
            "validation_rules": [
                "molecular_weight > 0",
                "half_life_hours > 0"
            ]
        }
    }
    
    # Write schema file
    schema_path = data_dir / "output_schema.yaml"
    with open(schema_path, 'w') as f:
        yaml.dump(schema_content, f, default_flow_style=False, sort_keys=False)
    
    print(f"Created schema file: {schema_path}")
    
    # Verify directories exist
    assert raw_dir.exists(), "data/raw directory not created"
    assert processed_dir.exists(), "data/processed directory not created"
    assert schema_path.exists(), "output_schema.yaml not created"
    
    print("Data directory setup complete.")

if __name__ == "__main__":
    main()