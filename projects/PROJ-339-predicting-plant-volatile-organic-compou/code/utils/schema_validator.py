"""
Schema validation utilities for the Plant VOC prediction pipeline.
Implements validation against the dataset.schema.yaml using Pydantic and jsonschema.
"""
import json
import yaml
import csv
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator, ValidationError
from datetime import datetime

# Define Pydantic models matching the YAML schema
class Sample(BaseModel):
    sample_id: str = Field(..., description="Unique identifier for the sample")
    species: str = Field(..., description="Scientific name of the plant species")
    tissue_type: str = Field(..., description="Type of plant tissue")
    collection_date: str = Field(..., description="Date of sample collection (YYYY-MM-DD)")
    experiment_id: Optional[str] = Field(None, description="Identifier for the experiment")
    source: Optional[str] = Field(None, description="Data source")
    accession_id: Optional[str] = Field(None, description="Original accession ID")

    @validator('collection_date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")
        return v

class GenomicFeature(BaseModel):
    sample_id: str = Field(..., description="Foreign key linking to Sample")
    gene_id: str = Field(..., description="Gene identifier")
    gene_symbol: Optional[str] = Field(None, description="Common gene symbol")
    tpm: float = Field(..., description="Transcripts Per Million normalized expression value")
    raw_count: int = Field(..., description="Raw read count before normalization")
    pathway: Optional[str] = Field(None, description="Associated metabolic pathway")
    family: Optional[str] = Field(None, description="Gene family")

class EnvironmentalFeature(BaseModel):
    sample_id: str = Field(..., description="Foreign key linking to Sample")
    temperature: float = Field(..., description="Temperature in Celsius")
    light_intensity: float = Field(..., description="Light intensity in µmol m⁻² s⁻¹")
    co2_level: float = Field(..., description="CO2 concentration in ppm")
    humidity: Optional[float] = Field(None, description="Relative humidity in %")
    stress_condition: Optional[str] = Field(None, description="Description of applied stress")
    duration_hours: Optional[float] = Field(None, description="Duration of stress exposure in hours")

class VOCProfile(BaseModel):
    sample_id: str = Field(..., description="Foreign key linking to Sample")
    compound_name: str = Field(..., description="Name of the VOC compound")
    cas_number: Optional[str] = Field(None, description="CAS registry number")
    emission_rate: float = Field(..., description="Emission rate")
    unit: str = Field(..., description="Unit of measurement")
    detection_limit: Optional[float] = Field(None, description="Limit of detection")
    compound_class: Optional[str] = Field(None, description="Chemical class")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_record(record: Dict[str, Any], record_type: str) -> bool:
    """
    Validate a single record (dict) against a specific Pydantic model.
    Returns True if valid, raises ValidationError if not.
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
    try:
        model(**record)
        return True
    except ValidationError as e:
        # Re-raise to allow caller to handle
        raise e

def validate_csv_dummy(csv_path: str, schema_path: str) -> bool:
    """
    Validate a dummy CSV file against the schema.
    Expects the CSV to have a 'record_type' column indicating the type of each row.
    Or validates the whole file as one type if specified.
    For this implementation, we assume a specific format:
    The CSV must contain headers matching one of the defined schemas.
    We will infer the type based on the headers present.
    """
    schema = load_schema(schema_path)
    definitions = schema.get('definitions', {})

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Read headers to determine type
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        # Determine which schema this matches
        matched_type = None
        for def_name, def_schema in definitions.items():
            required = def_schema.get('required', [])
            props = def_schema.get('properties', {})
            # Check if all required fields are in headers
            if all(field in headers for field in required):
                # Additional check: ensure headers match properties
                if all(field in props for field in headers):
                    matched_type = def_name
                    break

        if not matched_type:
            # Fallback: try to match by checking if headers are a subset of properties
            for def_name, def_schema in definitions.items():
                props = def_schema.get('properties', {})
                if all(field in props for field in headers):
                    matched_type = def_name
                    break

        if not matched_type:
            raise ValueError(f"Could not determine schema type for CSV with headers: {headers}")

    # Validate each row
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            try:
                validate_record(row, matched_type)
            except ValidationError as e:
                print(f"Validation error in row {i}: {e}")
                return False

    print(f"CSV {csv_path} validated successfully against {matched_type} schema.")
    return True

def generate_dummy_csv(output_path: str, record_type: str = 'Sample', count: int = 5) -> str:
    """
    Generate a dummy CSV file that conforms to the schema for verification.
    Returns the path to the generated file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if record_type == 'Sample':
        headers = ['sample_id', 'species', 'tissue_type', 'collection_date', 'experiment_id']
        rows = [
            ['S001', 'Arabidopsis thaliana', 'leaf', '2023-01-15', 'EXP01'],
            ['S002', 'Arabidopsis thaliana', 'flower', '2023-01-16', 'EXP01'],
            ['S003', 'Arabidopsis thaliana', 'root', '2023-01-17', 'EXP02'],
            ['S004', 'Arabidopsis thaliana', 'leaf', '2023-01-18', 'EXP02'],
            ['S005', 'Arabidopsis thaliana', 'leaf', '2023-01-19', 'EXP03'],
        ]
    elif record_type == 'GenomicFeature':
        headers = ['sample_id', 'gene_id', 'gene_symbol', 'tpm', 'raw_count', 'pathway']
        rows = [
            ['S001', 'AT1G01010', 'NAC1', 15.5, 120, 'Terpenoid'],
            ['S001', 'AT1G01020', 'NAC2', 2.3, 45, 'Terpenoid'],
            ['S002', 'AT1G01010', 'NAC1', 18.1, 130, 'Terpenoid'],
            ['S003', 'AT1G01030', 'NAC3', 5.0, 80, 'Lipid'],
            ['S004', 'AT1G01010', 'NAC1', 12.2, 95, 'Terpenoid'],
        ]
    elif record_type == 'EnvironmentalFeature':
        headers = ['sample_id', 'temperature', 'light_intensity', 'co2_level', 'humidity']
        rows = [
            ['S001', 25.0, 300.0, 400.0, 60.0],
            ['S002', 26.0, 350.0, 420.0, 55.0],
            ['S003', 24.0, 280.0, 390.0, 65.0],
            ['S004', 25.5, 310.0, 410.0, 58.0],
            ['S005', 25.0, 300.0, 400.0, 60.0],
        ]
    elif record_type == 'VOCProfile':
        headers = ['sample_id', 'compound_name', 'emission_rate', 'unit', 'compound_class']
        rows = [
            ['S001', 'Limonene', 150.5, 'ng g-1 h-1', 'Monoterpene'],
            ['S001', 'Pinene', 80.2, 'ng g-1 h-1', 'Monoterpene'],
            ['S002', 'Geraniol', 120.0, 'ng g-1 h-1', 'Monoterpene'],
            ['S003', 'Hexenal', 45.0, 'ng g-1 h-1', 'Green Leaf Volatile'],
            ['S004', 'Linalool', 95.5, 'ng g-1 h-1', 'Monoterpene'],
        ]
    else:
        raise ValueError(f"Unknown record type for generation: {record_type}")

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return str(path)

def main():
    """Main function to demonstrate schema validation."""
    import tempfile

    schema_path = "specs/001-predict-voc-profiles/contracts/dataset.schema.yaml"

    # Test 1: Generate and validate dummy CSVs for each type
    types = ['Sample', 'GenomicFeature', 'EnvironmentalFeature', 'VOCProfile']
    for t in types:
        dummy_path = generate_dummy_csv(f"data/raw/dummy_{t.lower()}.csv", t)
        print(f"Generated {dummy_path}")
        try:
            validate_csv_dummy(dummy_path, schema_path)
            print(f"Validation PASSED for {t}")
        except Exception as e:
            print(f"Validation FAILED for {t}: {e}")

    # Test 2: Validate a manually constructed record
    test_record = {
        "sample_id": "TEST001",
        "species": "Arabidopsis thaliana",
        "tissue_type": "leaf",
        "collection_date": "2023-10-27"
    }
    try:
        validate_record(test_record, "Sample")
        print("Manual record validation PASSED")
    except ValidationError as e:
        print(f"Manual record validation FAILED: {e}")

    print("Schema validation checks completed.")

if __name__ == "__main__":
    main()
