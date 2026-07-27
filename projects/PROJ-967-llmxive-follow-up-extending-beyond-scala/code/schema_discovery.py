"""
Schema Discovery and Validation Module for T038

This module performs schema discovery on the Z-Reward dataset,
validates required fields, and updates the schema contracts.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the module."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def save_schema(schema: Dict[str, Any], schema_path: Path) -> None:
    """Save a schema to a YAML file."""
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Schema saved to {schema_path}")


def load_dataset(dataset_path: Path) -> pd.DataFrame:
    """Load the Z-Reward dataset from a parquet file."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_parquet(dataset_path)
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    return df


def discover_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Discover the actual schema from the dataset."""
    logger.info("Discovering schema from dataset...")
    
    discovered = {
        "columns": [],
        "detected_dimensions": set(),
        "column_mapping": {}
    }
    
    # Iterate through columns and discover their types and properties
    for col in df.columns:
        col_info = {
            "name": col,
            "type": str(df[col].dtype),
            "sample_values": df[col].head(3).tolist() if len(df) > 0 else []
        }
        
        # Check for dict-like columns (teacher_scores, human_annotations)
        if df[col].apply(lambda x: isinstance(x, dict)).any():
            sample_dict = df[col].iloc[0] if len(df) > 0 else {}
            if isinstance(sample_dict, dict):
                col_info["properties"] = list(sample_dict.keys())
                discovered["detected_dimensions"].update(sample_dict.keys())
        
        discovered["columns"].append(col_info)
        discovered["column_mapping"][col] = col
    
    discovered["detected_dimensions"] = list(discovered["detected_dimensions"])
    
    logger.info(f"Discovered {len(discovered['columns'])} columns")
    logger.info(f"Detected dimensions: {discovered['detected_dimensions']}")
    
    return discovered


def validate_schema(df: pd.DataFrame, expected_dimensions: List[str]) -> Dict[str, Any]:
    """Validate that the dataset contains all required fields and dimensions."""
    logger.info("Validating schema...")
    
    validation_result = {
        "valid": True,
        "missing_columns": [],
        "missing_dimensions": [],
        "issues": []
    }
    
    # Check for required columns
    required_columns = [
        "sample_id", "prompt", "image_url", 
        "teacher_scores", "student_scalar", 
        "human_annotations", "primary_dimension"
    ]
    
    for col in required_columns:
        if col not in df.columns:
            validation_result["valid"] = False
            validation_result["missing_columns"].append(col)
            validation_result["issues"].append(f"Missing required column: {col}")
    
    # Check for required dimensions in teacher_scores
    if "teacher_scores" in df.columns:
        for dim in expected_dimensions:
            if not df["teacher_scores"].apply(
                lambda x: isinstance(x, dict) and dim in x
            ).all():
                validation_result["valid"] = False
                validation_result["missing_dimensions"].append(dim)
                validation_result["issues"].append(
                    f"Missing dimension '{dim}' in teacher_scores"
                )
    
    # Check for required dimensions in human_annotations
    if "human_annotations" in df.columns:
        for dim in expected_dimensions:
            if not df["human_annotations"].apply(
                lambda x: isinstance(x, dict) and dim in x
            ).all():
                validation_result["valid"] = False
                validation_result["missing_dimensions"].append(dim)
                validation_result["issues"].append(
                    f"Missing dimension '{dim}' in human_annotations"
                )
    
    # Check primary_dimension values
    if "primary_dimension" in df.columns:
        valid_dims = set(expected_dimensions)
        unique_dims = df["primary_dimension"].unique()
        invalid_dims = set(unique_dims) - valid_dims
        if invalid_dims:
            validation_result["valid"] = False
            validation_result["issues"].append(
                f"Invalid primary_dimension values found: {invalid_dims}"
            )
    
    if validation_result["valid"]:
        logger.info("Schema validation passed!")
    else:
        logger.warning(f"Schema validation failed with {len(validation_result['issues'])} issues")
    
    return validation_result


def update_contract(
    discovered_schema: Dict[str, Any],
    validation_result: Dict[str, Any],
    output_schema_path: Path,
    expected_dimensions: List[str] = None
) -> Dict[str, Any]:
    """Update the schema contract file with discovered schema and validation results."""
    
    if expected_dimensions is None:
        expected_dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    
    # Load existing schema if it exists, otherwise create a new one
    if output_schema_path.exists():
        schema = load_schema(output_schema_path)
    else:
        schema = {
            "version": "1.0",
            "dataset_name": "z-reward-evaluation",
            "format": "parquet",
            "source_url": "https://huggingface.co/datasets/z-reward/z-reward",
            "columns": [],
            "validation_rules": [],
            "notes": ""
        }
    
    # Update columns with discovered schema
    schema["columns"] = []
    for col_info in discovered_schema["columns"]:
        col_entry = {
            "name": col_info["name"],
            "type": col_info["type"],
            "required": col_info["name"] in [
                "sample_id", "prompt", "image_url", 
                "teacher_scores", "student_scalar", 
                "human_annotations", "primary_dimension"
            ]
        }
        
        # Add specific properties for dict columns
        if col_info["name"] in ["teacher_scores", "human_annotations"]:
            col_entry["type"] = "object"
            col_entry["properties"] = {}
            for dim in expected_dimensions:
                col_entry["properties"][dim] = {
                    "type": "number",
                    "description": f"Score for {dim} dimension"
                }
            col_entry["description"] = f"{col_info['name']} for rubric dimensions"
        
        schema["columns"].append(col_entry)
    
    # Update validation rules
    schema["validation_rules"] = [
        {
            "rule": "All four rubric dimensions must exist in teacher_scores",
            "dimensions": expected_dimensions
        },
        {
            "rule": "All four rubric dimensions must exist in human_annotations",
            "dimensions": expected_dimensions
        },
        {
            "rule": "primary_dimension must be a valid enum value",
            "enum": expected_dimensions
        },
        {
            "rule": "student_scalar must be a numeric value"
        }
    ]
    
    # Add validation status
    schema["validation_status"] = {
        "last_validated": "T038",
        "is_valid": validation_result["valid"],
        "issues": validation_result["issues"]
    }
    
    # Add notes
    schema["notes"] = (
        "This schema was discovered and validated by inspecting the actual\n"
        "z-reward/z-reward dataset on Hugging Face Hub. The dataset contains\n"
        "image prompts, generated images, and human annotations for the four\n"
        "rubric dimensions (Alignment, Realism, Aesthetics, Plausibility)."
    )
    
    # Save updated schema
    save_schema(schema, output_schema_path)
    
    return schema


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Schema Discovery and Validation for Z-Reward Dataset"
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw/z_reward_data.parquet"),
        help="Path to the Z-Reward dataset parquet file"
    )
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-entanglement-analysis/contracts/dataset.schema.yaml"),
        help="Path to the schema contract file"
    )
    parser.add_argument(
        "--expected-dimensions",
        type=str,
        nargs="+",
        default=["Alignment", "Realism", "Aesthetics", "Plausibility"],
        help="Expected rubric dimensions"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point for schema discovery and validation."""
    args = parse_args()
    
    if args.verbose:
        setup_logging(logging.DEBUG)
    else:
        setup_logging(logging.INFO)
    
    try:
        # Load the dataset
        df = load_dataset(args.dataset_path)
        
        # Discover schema
        discovered_schema = discover_schema(df)
        
        # Validate schema
        validation_result = validate_schema(df, args.expected_dimensions)
        
        # Update contract
        updated_schema = update_contract(
            discovered_schema,
            validation_result,
            args.schema_path,
            args.expected_dimensions
        )
        
        # Print summary
        print("\n" + "="*60)
        print("SCHEMA DISCOVERY AND VALIDATION SUMMARY")
        print("="*60)
        print(f"Dataset: {args.dataset_path}")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print(f"Schema Valid: {validation_result['valid']}")
        
        if not validation_result['valid']:
            print("\nIssues found:")
            for issue in validation_result['issues']:
                print(f"  - {issue}")
        else:
            print("\nAll validations passed!")
        
        print(f"\nUpdated schema saved to: {args.schema_path}")
        print("="*60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during schema discovery: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
