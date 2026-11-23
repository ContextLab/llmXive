"""
Script to validate the schema of generated parquet files.
Required by T013d.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

def validate_schema(parquet_path: str) -> bool:
    """Verify the generated parquet matches the required schema.
    
    Required columns:
    - node_features: List[List[float32]]
    - edge_features: List[List[float32]]
    - target_moduli: Dict[str, float64]
    - family_id: str
    """
    if not Path(parquet_path).exists():
        logging.error(f"File not found: {parquet_path}")
        return False

    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        logging.error(f"Failed to read parquet: {e}")
        return False

    required_cols = ["node_features", "edge_features", "target_moduli", "family_id"]
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        logging.error(f"Schema validation failed: Missing columns: {missing}")
        return False

    # Type checks (best effort for parquet)
    if len(df) > 0:
        # Check node_features is list-like
        try:
            val = df.iloc[0]["node_features"]
            if not isinstance(val, (list, tuple, pd.Series, type(df.iloc[0]["node_features"].__class__.__bases__[0]() if hasattr(df.iloc[0]["node_features"], '__class__') else []))):
                # Fallback check for numpy arrays or lists
                import numpy as np
                if not isinstance(val, np.ndarray) and not isinstance(val, list):
                    logging.error("Schema validation failed: node_features is not a list/array")
                    return False
        except Exception as e:
            logging.error(f"Schema validation error on node_features: {e}")
            return False
        
        # Check edge_features is list-like
        try:
            val = df.iloc[0]["edge_features"]
            import numpy as np
            if not isinstance(val, (list, tuple, np.ndarray)):
                logging.error("Schema validation failed: edge_features is not a list/array")
                return False
        except Exception as e:
            logging.error(f"Schema validation error on edge_features: {e}")
            return False
        
        # Check target_moduli is dict-like
        try:
            val = df.iloc[0]["target_moduli"]
            if not isinstance(val, (dict, type({}))):
                # Parquet often stores dicts as generic objects
                if not hasattr(val, 'keys'):
                    logging.error("Schema validation failed: target_moduli is not a dict")
                    return False
        except Exception as e:
            logging.error(f"Schema validation error on target_moduli: {e}")
            return False
        
        # Check family_id is string
        try:
            val = df.iloc[0]["family_id"]
            if not isinstance(val, str):
                logging.error(f"Schema validation failed: family_id is not a string (got {type(val)})")
                return False
        except Exception as e:
            logging.error(f"Schema validation error on family_id: {e}")
            return False

    logging.info("Schema validation passed.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Validate schema of a parquet file.")
    parser.add_argument("--input", type=str, required=True, help="Path to the parquet file to validate.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if validate_schema(args.input):
        logging.info("Validation successful.")
        sys.exit(0)
    else:
        logging.error("Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
