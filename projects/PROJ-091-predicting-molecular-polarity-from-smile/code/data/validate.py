import sys
import os
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import json

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.preprocess_2d import get_2d_descriptor_names
from utils.validators import validate_dataset_schema

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _load_descriptor_names_json(json_path: Path) -> List[str]:
    """
    Load descriptor names from a JSON file.
    The JSON is expected to be a list of descriptor name strings.
    """
    if not json_path.is_file():
        raise FileNotFoundError(f"Descriptor names JSON not found: {json_path}")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Descriptor names JSON must contain a list, got {type(data)}")
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to read descriptor names from {json_path}: {e}")

def validate_processed_descriptors(filepath: str, expected_columns: int = None) -> Tuple[bool, str]:
    """
    Validate the processed descriptors parquet file.

    Args:
        filepath: Path to the descriptors parquet file
        expected_columns: Expected number of columns (smiles + target + descriptors)

    Returns:
        Tuple of (success: bool, message: str)
    """
    logger.info(f"Validating descriptors file: {filepath}")

    # Check file existence
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"

    try:
        # Load the parquet file
        df = pd.read_parquet(filepath)
        logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    except Exception as e:
        return False, f"Failed to load parquet file: {str(e)}"

    # Check required base columns
    required_base = ['smiles', 'target']
    missing_base = [col for col in required_base if col not in df.columns]
    if missing_base:
        return False, f"Missing required base columns: {missing_base}"

    # Check for forbidden columns (TPSA, 3D-derived)
    forbidden_patterns = ['TPSA', 'TPSA_E', 'Get3DConformer', 'EmbedMolecule']
    forbidden_found = []
    for col in df.columns:
        for pattern in forbidden_patterns:
            if pattern in col:
                forbidden_found.append(col)
                break

    if forbidden_found:
        return False, f"Found forbidden columns (3D/TPSA): {forbidden_found}"

    # Check descriptor columns
    descriptor_cols = [col for col in df.columns if col.startswith('desc_')]
    if len(descriptor_cols) == 0:
        return False, "No descriptor columns found (expected columns starting with 'desc_')"

    # Validate data types
    if df['target'].dtype not in [np.float32, np.float64, int, float]:
        return False, f"Target column has invalid dtype: {df['target'].dtype}"

    # Check for NaN in required columns
    nan_count = df['target'].isna().sum()
    if nan_count > 0:
        logger.warning(f"Found {nan_count} NaN values in target column")

    # Dynamic column count validation
    if expected_columns is not None:
        actual_columns = len(df.columns)
        if actual_columns != expected_columns:
            return False, f"Column count mismatch: expected {expected_columns}, got {actual_columns}"
        logger.info(f"Column count validation passed: {actual_columns} columns")
    else:
        # Derive expected count from descriptor_names.json
        descriptor_json_path = Path("data/processed/descriptor_names.json")
        try:
            descriptor_names = _load_descriptor_names_json(descriptor_json_path)
        except Exception as e:
            return False, f"Unable to determine expected descriptor count: {e}"

        expected = 2 + len(descriptor_names)  # smiles + target + descriptors
        actual = len(df.columns)

        if actual != expected:
            return False, (
                f"Column count mismatch: expected {expected} "
                f"(2 + {len(descriptor_names)} descriptors), got {actual}"
            )
        logger.info(
            f"Dynamic column count validation passed: {actual} == 2 + {len(descriptor_names)}"
        )

    # Check for NaN in descriptor columns (should be handled by preprocess_2d)
    nan_descriptors = df[descriptor_cols].isna().sum().sum()
    if nan_descriptors > 0:
        logger.warning(f"Found {nan_descriptors} NaN values in descriptor columns")

    # Validate schema using the contract validator
    try:
        # Convert to dict for validation
        sample_row = df.head(1).to_dict('records')[0]
        validate_dataset_schema(sample_row)
        logger.info("Schema validation passed")
    except Exception as e:
        return False, f"Schema validation failed: {str(e)}"

    return True, (
        f"Validation successful: {len(df)} rows, {len(df.columns)} columns "
        f"(2 base + {len(descriptor_cols)} descriptors)"
    )

def main():
    parser = argparse.ArgumentParser(
        description='Validate processed descriptors file'
    )
    # Positional argument for the parquet file (as required by verification)
    parser.add_argument(
        'filepath',
        type=str,
        help='Path to the descriptors parquet file'
    )
    parser.add_argument(
        '--expected-columns',
        type=int,
        default=None,
        help='Expected number of columns (optional, derived if not provided)'
    )

    args = parser.parse_args()

    success, message = validate_processed_descriptors(args.filepath, args.expected_columns)

    if success:
        logger.info(f"SUCCESS: {message}")
        sys.exit(0)
    else:
        logger.error(f"FAILED: {message}")
        sys.exit(1)

if __name__ == '__main__':
    main()