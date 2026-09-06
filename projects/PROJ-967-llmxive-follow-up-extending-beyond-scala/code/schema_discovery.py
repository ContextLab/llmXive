import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Add project root to path if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.setup_directories import setup_data_directories

logger = logging.getLogger(__name__)

# Constants
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
CONTRACTS_PATH = PROJECT_ROOT / "specs" / "001-llmxive-follow-up-extending-beyond-scala" / "contracts"
SCHEMA_FILE = CONTRACTS_PATH / "dataset.schema.yaml"
OUTPUT_SCHEMA_FILE = CONTRACTS_PATH / "output.schema.yaml"

# Expected dimensions for teacher scores and human annotations
RUBRIC_DIMENSIONS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]


def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def save_schema(schema: Dict[str, Any], schema_path: Path):
    """Save a schema to a YAML file."""
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    with open(schema_path, "w") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)


def load_dataset(file_path: Path) -> pd.DataFrame:
    """Load the dataset from a parquet file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    # Try to load as parquet first
    try:
        df = pd.read_parquet(file_path)
        return df
    except Exception as e:
        logger.warning(f"Failed to load as parquet: {e}")
    
    # Try CSV as fallback
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset from {file_path}: {e}")


def discover_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Discover the actual schema from the dataframe."""
    fields = []
    
    for col in df.columns:
        field_info = {
            "name": col,
            "type": str(df[col].dtype),
            "nullable": df[col].isna().any(),
            "sample_values": df[col].dropna().head(3).tolist() if not df[col].isna().all() else []
        }
        
        # Detect nested structures
        if df[col].apply(lambda x: isinstance(x, dict)).any():
            field_info["type"] = "object"
            # Try to extract properties if it's a dict
            sample = df[col].dropna().iloc[0] if not df[col].isna().all() else {}
            if isinstance(sample, dict):
                field_info["properties"] = list(sample.keys())
        
        fields.append(field_info)
    
    return {
        "schema_version": "1.0",
        "discovered_at": pd.Timestamp.now().isoformat(),
        "source_file": str(file_path),
        "row_count": len(df),
        "fields": fields
    }


def validate_schema(discovered: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """Validate discovered schema against the template."""
    validation_result = {
        "is_valid": True,
        "discrepancies": [],
        "missing_fields": [],
        "extra_fields": [],
        "type_mismatches": []
    }
    
    template_fields = {f["name"]: f for f in template.get("fields", [])}
    discovered_fields = {f["name"]: f for f in discovered.get("fields", [])}
    
    # Check for missing required fields
    for name, template_field in template_fields.items():
        if name not in discovered_fields:
            validation_result["is_valid"] = False
            validation_result["missing_fields"].append(name)
            validation_result["discrepancies"].append(f"Missing required field: {name}")
        
        elif template_field.get("type") and template_field["type"] != "any":
            # Check type compatibility (simplified)
            discovered_type = discovered_fields[name].get("type", "")
            template_type = template_field["type"]
            
            # Handle object types with properties
            if template_type == "object" and template_field.get("properties"):
                if discovered_fields[name].get("type") != "object":
                    validation_result["is_valid"] = False
                    validation_result["type_mismatches"].append({
                        "field": name,
                        "expected": template_type,
                        "found": discovered_type
                    })
                else:
                    # Check properties
                    template_props = set(template_field["properties"])
                    discovered_props = set(discovered_fields[name].get("properties", []))
                    missing_props = template_props - discovered_props
                    if missing_props:
                        validation_result["is_valid"] = False
                        validation_result["discrepancies"].append(
                            f"Field '{name}' missing properties: {missing_props}"
                        )
            
            elif discovered_type != template_type:
                # Allow some flexibility for numeric types
                numeric_types = {"int64", "float64", "int32", "float32", "int", "float"}
                if not (template_type in numeric_types and discovered_type in numeric_types):
                    validation_result["is_valid"] = False
                    validation_result["type_mismatches"].append({
                        "field": name,
                        "expected": template_type,
                        "found": discovered_type
                    })
    
    # Check for extra fields not in template
    extra_fields = set(discovered_fields.keys()) - set(template_fields.keys())
    if extra_fields:
        validation_result["extra_fields"] = list(extra_fields)
        logger.info(f"Extra fields found (not in template): {extra_fields}")
    
    return validation_result


def update_contract(discovered_schema: Dict[str, Any], validation_result: Dict[str, Any], target_path: Path):
    """Update the contract schema file with the discovered and validated schema."""
    # Create the final schema based on discovered fields
    final_schema = {
        "schema_version": "1.0",
        "fields": []
    }
    
    # Add discovered fields, mapping to the template structure where possible
    template_fields = {f["name"]: f for f in load_schema(SCHEMA_FILE).get("fields", [])}
    
    for field in discovered_schema["fields"]:
        field_name = field["name"]
        final_field = {
            "name": field_name,
            "type": field.get("type", "string")
        }
        
        # Add properties if it's an object type
        if field.get("type") == "object" and field.get("properties"):
            final_field["properties"] = {}
            for prop in field["properties"]:
                final_field["properties"][prop] = "float"  # Default to float for scores
        
        final_schema["fields"].append(final_field)
    
    # Save the updated schema
    save_schema(final_schema, target_path)
    logger.info(f"Updated schema saved to {target_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation")
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Path to the input dataset file (parquet or csv). Defaults to auto-detection."
    )
    parser.add_argument(
        "--template-schema",
        type=str,
        default=str(SCHEMA_FILE),
        help="Path to the template schema YAML file."
    )
    parser.add_argument(
        "--output-schema",
        type=str,
        default=str(SCHEMA_FILE),
        help="Path to save the updated schema."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_logging()
    logger.info("Starting schema discovery and validation...")
    
    # Setup directories
    setup_data_directories()
    
    # Determine input file
    input_file = Path(args.input_file) if args.input_file else None
    
    if not input_file:
        # Auto-detect: check for z_reward.parquet first, then synthetic
        potential_files = [
            RAW_DATA_PATH / "z_reward.parquet",
            RAW_DATA_PATH / "z_reward_synthetic.parquet",
            RAW_DATA_PATH / "mock_z_reward.parquet"
        ]
        for candidate in potential_files:
            if candidate.exists():
                input_file = candidate
                logger.info(f"Auto-detected input file: {input_file}")
                break
        
        if not input_file:
            raise FileNotFoundError(
                "No dataset file found. Please provide --input-file or ensure one of the "
                "expected files exists in data/raw/."
            )
    
    logger.info(f"Loading dataset from: {input_file}")
    
    # Load dataset
    try:
        df = load_dataset(input_file)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)
    
    # Discover schema
    logger.info("Discovering schema...")
    discovered_schema = discover_schema(df)
    
    # Load template schema
    template_schema_path = Path(args.template_schema)
    if not template_schema_path.exists():
        logger.warning(f"Template schema not found at {template_schema_path}, creating from scratch")
        template_schema = {"schema_version": "1.0", "fields": []}
    else:
        template_schema = load_schema(template_schema_path)
    
    # Validate against template
    logger.info("Validating schema against template...")
    validation_result = validate_schema(discovered_schema, template_schema)
    
    # Log validation results
    if validation_result["is_valid"]:
        logger.info("✓ Schema validation PASSED")
    else:
        logger.warning("✗ Schema validation FAILED")
        logger.warning(f"Missing fields: {validation_result['missing_fields']}")
        logger.warning(f"Type mismatches: {validation_result['type_mismatches']}")
        logger.warning(f"Discrepancies: {validation_result['discrepancies']}")
    
    # Check for critical mismatches (missing rubric dimensions)
    critical_missing = []
    for dim in RUBRIC_DIMENSIONS:
        # Check if dimension exists in teacher_scores or human_annotations
        found = False
        for field in discovered_schema["fields"]:
            if field["name"] in ["teacher_scores", "human_annotations"]:
                if field.get("properties") and dim in field.get("properties", []):
                    found = True
                    break
            elif field["name"] == dim:
                found = True
                break
        
        if not found:
            critical_missing.append(dim)
    
    if critical_missing:
        error_msg = f"CRITICAL: Missing rubric dimensions: {critical_missing}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Update contract if there are discrepancies
    output_schema_path = Path(args.output_schema)
    if validation_result["discrepancies"] or validation_result["missing_fields"]:
        logger.info(f"Discrepancies found. Updating contract schema at {output_schema_path}")
        update_contract(discovered_schema, validation_result, output_schema_path)
    else:
        logger.info("No discrepancies found. Contract schema remains unchanged.")
    
    # Save discovery report
    report = {
        "input_file": str(input_file),
        "discovered_schema": discovered_schema,
        "validation_result": validation_result,
        "status": "valid" if validation_result["is_valid"] else "invalid"
    }
    
    report_path = PROJECT_ROOT / "results" / "schema_discovery_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        import json
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Schema discovery report saved to: {report_path}")
    logger.info("Schema discovery and validation completed.")
    
    return 0 if validation_result["is_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
