import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import yaml

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("schema_discovery")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the provisional schema contract."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def save_schema(schema: Dict[str, Any], output_path: Path) -> None:
    """Save the validated schema to a YAML file."""
    with open(output_path, "w") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

def load_dataset(data_path: Path, is_mock: bool = False) -> pd.DataFrame:
    """Load the dataset from the specified path."""
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {data_path}")
    logger.info(f"Loading dataset from {data_path}")
    if data_path.suffix == ".parquet":
        df = pd.read_parquet(data_path)
    elif data_path.suffix == ".csv":
        df = pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")
    return df

def discover_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Discover the actual schema from the dataframe."""
    fields = []
    for col in df.columns:
        field_type = str(df[col].dtype)
        # Map pandas types to logical types
        if "float" in field_type:
            logical_type = "float"
        elif "int" in field_type:
            logical_type = "integer"
        elif "object" in field_type:
            # Check if it might be a nested object (like teacher_scores)
            sample_val = df[col].iloc[0] if len(df) > 0 else None
            if isinstance(sample_val, dict):
                logical_type = "object"
            else:
                logical_type = "string"
        else:
            logical_type = field_type

        field_info = {
            "name": col,
            "type": logical_type
        }

        # Handle nested objects (e.g., teacher_scores, human_annotations)
        if logical_type == "object" and isinstance(sample_val, dict):
            properties = {}
            for key, val in sample_val.items():
                if isinstance(val, float):
                    prop_type = "float"
                elif isinstance(val, int):
                    prop_type = "integer"
                else:
                    prop_type = "string"
                properties[key] = {"type": prop_type}
            field_info["properties"] = properties

        fields.append(field_info)

    return {
        "schema_version": "1.0",
        "fields": fields,
        "row_count": len(df),
        "column_count": len(df.columns)
    }

def validate_schema(discovered: Dict[str, Any], provisional: Dict[str, Any]) -> Dict[str, Any]:
    """Validate discovered schema against provisional template and report discrepancies."""
    discrepancies = []
    required_fields = {
        "prompt", "image_url", "student_scalar", "primary_dimension"
    }
    required_nested = {
        "teacher_scores": {"Alignment", "Realism", "Aesthetics", "Plausibility"},
        "human_annotations": {"Alignment", "Realism", "Aesthetics", "Plausibility"}
    }

    discovered_map = {f["name"]: f for f in discovered["fields"]}

    # Check required top-level fields
    for req in required_fields:
        if req not in discovered_map:
            discrepancies.append(f"Missing required field: {req}")

    # Check required nested fields
    for nested_name, required_keys in required_nested.items():
        if nested_name not in discovered_map:
            discrepancies.append(f"Missing required nested field: {nested_name}")
        else:
            nested_props = discovered_map[nested_name].get("properties", {})
            missing_keys = required_keys - set(nested_props.keys())
            if missing_keys:
                discrepancies.append(f"Missing keys in {nested_name}: {missing_keys}")

    # Compare types where both exist
    for prov_field in provisional.get("fields", []):
        prov_name = prov_field["name"]
        if prov_name in discovered_map:
            disc_field = discovered_map[prov_name]
            if prov_field["type"] != disc_field["type"]:
                discrepancies.append(
                    f"Type mismatch for {prov_name}: "
                    f"expected {prov_field['type']}, got {disc_field['type']}"
                )

    return {
        "valid": len(discrepancies) == 0,
        "discrepancies": discrepancies,
        "discovered_schema": discovered
    }

def update_contract(discovered: Dict[str, Any], output_path: Path) -> None:
    """Update the contract with the discovered schema."""
    # We use the discovered schema as the validated schema
    validated_schema = {
        "schema_version": "1.0",
        "fields": discovered["fields"],
        "validated_at": "auto-discovered",
        "row_count": discovered.get("row_count", 0),
        "column_count": discovered.get("column_count", 0)
    }
    save_schema(validated_schema, output_path)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation")
    parser.add_argument(
        "--input-data",
        type=str,
        default="data/raw/z_reward.parquet",
        help="Path to the raw dataset file"
    )
    parser.add_argument(
        "--provisional-schema",
        type=str,
        default="specs/001-llmxive-entanglement-analysis/contracts/dataset.schema.yaml",
        help="Path to the provisional schema contract"
    )
    parser.add_argument(
        "--output-schema",
        type=str,
        default="specs/001-llmxive-entanglement-analysis/contracts/dataset.validated.schema.yaml",
        help="Path to save the validated schema"
    )
    parser.add_argument(
        "--use-mock-data",
        action="store_true",
        help="Use mock data path if real data not found"
    )
    return parser.parse_args()

def main():
    global logger
    logger = setup_logging()
    args = parse_args()

    data_path = Path(args.input_data)
    provisional_path = Path(args.provisional_schema)
    output_path = Path(args.output_schema)

    # Fallback to mock data if requested and real not found
    if args.use_mock_data and not data_path.exists():
        mock_path = Path("data/raw/mock_z_reward.parquet")
        if mock_path.exists():
            logger.info(f"Real data not found, using mock data: {mock_path}")
            data_path = mock_path
        else:
            logger.error("Mock data also not found. Cannot proceed.")
            sys.exit(1)

    try:
        # Load schema
        provisional_schema = load_schema(provisional_path)
        logger.info(f"Loaded provisional schema from {provisional_path}")

        # Load dataset
        df = load_dataset(data_path)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")

        # Discover schema
        discovered_schema = discover_schema(df)
        logger.info("Schema discovery completed")

        # Validate
        validation_result = validate_schema(discovered_schema, provisional_schema)

        if validation_result["valid"]:
            logger.info("Schema validation PASSED. No discrepancies found.")
        else:
            logger.warning("Schema validation found discrepancies:")
            for disc in validation_result["discrepancies"]:
                logger.warning(f"  - {disc}")

            # Check for critical mismatches (missing rubric dimensions)
            critical = [d for d in validation_result["discrepancies"] if "Missing" in d]
            if critical:
                logger.error("CRITICAL: Missing required fields or dimensions. Pipeline cannot proceed.")
                sys.exit(1)

        # Update contract
        update_contract(discovered_schema, output_path)
        logger.info(f"Validated schema saved to {output_path}")

        # Print summary
        logger.info("=== Schema Discovery Summary ===")
        logger.info(f"Total fields discovered: {len(discovered_schema['fields'])}")
        for field in discovered_schema["fields"]:
            logger.info(f"  - {field['name']}: {field['type']}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
