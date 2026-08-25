"""
Utility module for validating data against the dataset schema.
Implements T007a verification: Validate schema against a dummy CSV using pydantic/jsonschema.
"""
import json
import yaml
import csv
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from datetime import date

# Define Pydantic models matching the YAML schema for runtime validation
class Sample(BaseModel):
    sample_id: str
    species: str
    tissue_type: str
    collection_date: date
    experiment_id: Optional[str] = None
    replicate_id: Optional[int] = None
    treatment_condition: Optional[str] = None

class GenomicFeature(BaseModel):
    sample_id: str
    gene_id: str
    tpm_value: float
    gene_name: Optional[str] = None
    pathway_family: Optional[str] = None

class EnvironmentalFeature(BaseModel):
    sample_id: str
    temperature: float
    light_intensity: float
    co2_level: float
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None

class VOCProfile(BaseModel):
    sample_id: str
    compound_id: str
    concentration: float
    compound_name: Optional[str] = None
    unit: Optional[str] = None
    detection_limit: Optional[float] = None

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_record(record: Dict[str, Any], record_type: str) -> bool:
    """
    Validate a single dictionary record against its corresponding Pydantic model.
    Returns True if valid, raises ValidationError if invalid.
    """
    model_map = {
        'Sample': Sample,
        'GenomicFeature': GenomicFeature,
        'EnvironmentalFeature': EnvironmentalFeature,
        'VOCProfile': VOCProfile
    }

    if record_type not in model_map:
        raise ValueError(f"Unknown record type: {record_type}")

    model = model_map[record_type]
    # Pydantic v2 handles dict conversion automatically
    try:
        model(**record)
        return True
    except ValidationError as e:
        print(f"Validation failed for {record_type}: {e}")
        raise

def validate_csv_dummy(csv_path: str, schema_path: str) -> Dict[str, Any]:
    """
    Validate a dummy CSV file against the schema.
    Expects the CSV to have a 'record_type' column to distinguish schemas.
    """
    schema = load_schema(schema_path)
    results = {
        'total_records': 0,
        'valid_records': 0,
        'invalid_records': 0,
        'errors': []
    }

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dummy CSV not found: {csv_path}")

    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results['total_records'] += 1
            record_type = row.get('record_type')
            if not record_type:
                results['invalid_records'] += 1
                results['errors'].append(f"Row {results['total_records']}: Missing 'record_type'")
                continue

            # Remove the helper column before validation
            record_data = {k: v for k, v in row.items() if k != 'record_type'}
            
            # Convert date string if present
            if 'collection_date' in record_data:
                try:
                    record_data['collection_date'] = date.fromisoformat(record_data['collection_date'])
                except ValueError:
                    pass # Let pydantic handle the error

            try:
                validate_record(record_data, record_type)
                results['valid_records'] += 1
            except (ValidationError, ValueError) as e:
                results['invalid_records'] += 1
                results['errors'].append(f"Row {results['total_records']} ({record_type}): {str(e)}")

    return results

def generate_dummy_csv(output_path: str) -> None:
    """
    Generate a dummy CSV file for validation testing.
    Creates one valid example for each schema type.
    """
    headers = ['record_type', 'sample_id', 'species', 'tissue_type', 'collection_date', 
               'gene_id', 'tpm_value', 'temperature', 'light_intensity', 'co2_level',
               'compound_id', 'concentration']
    
    rows = [
        {
            'record_type': 'Sample',
            'sample_id': 'S001',
            'species': 'Arabidopsis thaliana',
            'tissue_type': 'leaf',
            'collection_date': '2023-05-15',
            'gene_id': '', 'tpm_value': '', 'temperature': '', 'light_intensity': '', 'co2_level': '',
            'compound_id': '', 'concentration': ''
        },
        {
            'record_type': 'GenomicFeature',
            'sample_id': 'S001',
            'species': '', 'tissue_type': '', 'collection_date': '',
            'gene_id': 'AT1G01010', 'tpm_value': 12.5,
            'temperature': '', 'light_intensity': '', 'co2_level': '',
            'compound_id': '', 'concentration': ''
        },
        {
            'record_type': 'EnvironmentalFeature',
            'sample_id': 'S001',
            'species': '', 'tissue_type': '', 'collection_date': '',
            'gene_id': '', 'tpm_value': '',
            'temperature': 24.5, 'light_intensity': 400.0, 'co2_level': 410.0,
            'compound_id': '', 'concentration': ''
        },
        {
            'record_type': 'VOCProfile',
            'sample_id': 'S001',
            'species': '', 'tissue_type': '', 'collection_date': '',
            'gene_id': '', 'tpm_value': '',
            'temperature': '', 'light_intensity': '', 'co2_level': '',
            'compound_id': '123-45-6', 'concentration': 5.2
        }
    ]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

def main():
    """Main entry point for schema validation."""
    import sys
    from pathlib import Path

    # Determine paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    schema_path = project_root / 'specs' / '001-predict-voc-profiles' / 'contracts' / 'dataset.schema.yaml'
    dummy_csv_path = project_root / 'data' / 'raw' / 'dummy_validation.csv'

    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        sys.exit(1)

    print(f"Generating dummy CSV at {dummy_csv_path}...")
    generate_dummy_csv(str(dummy_csv_path))

    print(f"Validating {dummy_csv_path} against {schema_path}...")
    try:
        results = validate_csv_dummy(str(dummy_csv_path), str(schema_path))
        print(json.dumps(results, indent=2))
        
        if results['invalid_records'] > 0:
            print("Validation FAILED.")
            sys.exit(1)
        else:
            print("Validation SUCCESSFUL.")
            sys.exit(0)
    except Exception as e:
        print(f"Validation process failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
