"""
T032: Validate output against contracts/dataset.schema.yaml

This script validates the final dataset produced by User Story 2
against the dataset schema defined in contracts/dataset.schema.yaml.

It checks:
1. File existence
2. Schema compliance using jsonschema
3. Data integrity (no nulls in required columns)
4. Value ranges for emotional_intensity (1-5)
"""
import os
import sys
import json
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from jsonschema import validate, ValidationError, Draft7Validator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (assumed to be two levels up from code/analysis)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# File paths
DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "final_dataset.csv"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
REPORT_PATH = PROJECT_ROOT / "outputs" / "reports" / "validation_emotion_output.json"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load YAML schema from file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_dataset(dataset_path: Path) -> pd.DataFrame:
    """Load the final dataset CSV."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    return df

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate dataframe against JSON schema.
    Returns validation report with pass/fail status and details.
    """
    report = {
        "schema_validation": {
            "passed": True,
            "errors": []
        },
        "data_integrity": {
            "passed": True,
            "issues": []
        },
        "value_ranges": {
            "passed": True,
            "issues": []
        }
    }
    
    # Convert dataframe to list of records for JSON schema validation
    records = df.to_dict('records')
    
    # Validate each record against schema
    validator = Draft7Validator(schema)
    
    for i, record in enumerate(records):
        errors = list(validator.iter_errors(record))
        if errors:
            report["schema_validation"]["passed"] = False
            for error in errors:
                report["schema_validation"]["errors"].append({
                    "row": i,
                    "message": error.message,
                    "path": list(error.path) if error.path else []
                })
    
    # Data integrity checks: required columns should not have nulls
    required_columns = schema.get("required", [])
    if "properties" in schema:
        required_columns = [
            prop for prop, props in schema["properties"].items()
            if props.get("required", False) or prop in required_columns
        ]
    
    for col in required_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                report["data_integrity"]["passed"] = False
                report["data_integrity"]["issues"].append({
                    "column": col,
                    "null_count": int(null_count),
                    "message": f"Column '{col}' has {null_count} null values"
                })
        else:
            report["data_integrity"]["passed"] = False
            report["data_integrity"]["issues"].append({
                "column": col,
                "message": f"Required column '{col}' is missing from dataset"
            })
    
    # Value range checks for emotional_intensity
    if "emotional_intensity" in df.columns:
        intensity_col = df["emotional_intensity"]
        if intensity_col.dtype in ['int64', 'float64', 'int32', 'float32']:
            min_val = intensity_col.min()
            max_val = intensity_col.max()
            
            if min_val < 1 or max_val > 5:
                report["value_ranges"]["passed"] = False
                report["value_ranges"]["issues"].append({
                    "column": "emotional_intensity",
                    "min_value": float(min_val),
                    "max_value": float(max_val),
                    "message": f"emotional_intensity values must be in range [1, 5], found [{min_val}, {max_val}]"
                })
            
            # Check for non-integer values if expected to be integer
            if not pd.api.types.is_integer_dtype(intensity_col):
                non_integers = (intensity_col % 1 != 0).sum()
                if non_integers > 0:
                    report["value_ranges"]["passed"] = False
                    report["value_ranges"]["issues"].append({
                        "column": "emotional_intensity",
                        "non_integer_count": int(non_integers),
                        "message": f"emotional_intensity should be integer values, found {non_integers} non-integers"
                    })
    
    return report

def save_report(report: Dict[str, Any], report_path: Path) -> None:
    """Save validation report to JSON file."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Validation report saved to: {report_path}")

def main():
    """Main validation function."""
    logger.info("Starting T032: Validate emotion output against schema")
    
    try:
        # Load schema
        logger.info(f"Loading schema from: {SCHEMA_PATH}")
        schema = load_schema(SCHEMA_PATH)
        
        # Load dataset
        logger.info(f"Loading dataset from: {DATASET_PATH}")
        df = load_dataset(DATASET_PATH)
        
        # Validate
        logger.info("Validating dataset against schema...")
        validation_report = validate_schema(df, schema)
        
        # Save report
        save_report(validation_report, REPORT_PATH)
        
        # Print summary
        logger.info("=" * 60)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        all_passed = True
        
        for section, data in validation_report.items():
            status = "✓ PASSED" if data["passed"] else "✗ FAILED"
            logger.info(f"{section}: {status}")
            
            if not data["passed"]:
                all_passed = False
                if "errors" in data and data["errors"]:
                    for err in data["errors"][:5]:  # Show first 5 errors
                        logger.info(f"  - {err}")
                if "issues" in data and data["issues"]:
                    for issue in data["issues"][:5]:  # Show first 5 issues
                        logger.info(f"  - {issue}")
        
        logger.info("=" * 60)
        
        if all_passed:
            logger.info("✓ ALL VALIDATIONS PASSED")
            return 0
        else:
            logger.warning("✗ SOME VALIDATIONS FAILED")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValidationError as e:
        logger.error(f"Schema validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())