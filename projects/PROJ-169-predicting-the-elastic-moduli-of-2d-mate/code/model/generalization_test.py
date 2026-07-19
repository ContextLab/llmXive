import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import pandas as pd
import numpy as np

from utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None if it doesn't exist."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {path}: {e}")
        return None

def save_json(data: Dict[str, Any], path: Path) -> None:
    """Save a dictionary to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved results to {path}")

def verify_family_disjoint(
    train_indices: List[Dict[str, Any]],
    test_indices: List[Dict[str, Any]],
    graph_df: pd.DataFrame
) -> bool:
    """
    Verify that no family_id appears in both train and test sets.
    Returns True if disjoint, False otherwise.
    """
    train_families = set()
    for item in train_indices:
        fid = item.get('family_id')
        if fid:
            train_families.add(fid)

    test_families = set()
    for item in test_indices:
        fid = item.get('family_id')
        if fid:
            test_families.add(fid)

    overlap = train_families.intersection(test_families)
    if overlap:
        logger.error(f"SC-002 Violation: Family overlap detected in split. Overlapping families: {overlap}")
        return False
    
    # Additional check: ensure all test IDs actually exist in the dataframe
    # and map to the expected family_ids (sanity check on data integrity)
    graph_ids = set(graph_df['material_id'].unique())
    test_ids = {item['id'] for item in test_indices}
    
    missing_ids = test_ids - graph_ids
    if missing_ids:
        logger.error(f"Data Integrity Error: Test indices contain IDs not found in graphs_v1.parquet: {missing_ids}")
        return False

    logger.info(f"Family disjoint check passed. Train families: {len(train_families)}, Test families: {len(test_families)}")
    return True

def load_graphs_from_parquet(parquet_path: Path) -> pd.DataFrame:
    """Load the processed graphs parquet file."""
    if not parquet_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {parquet_path}")
    logger.info(f"Loading graphs from {parquet_path}")
    return pd.read_parquet(parquet_path)

def build_family_mapping(graph_df: pd.DataFrame) -> Dict[str, str]:
    """Build a mapping from material_id to family_id."""
    if 'material_id' not in graph_df.columns or 'family_id' not in graph_df.columns:
        raise ValueError("Graph dataframe missing 'material_id' or 'family_id' columns")
    return dict(zip(graph_df['material_id'], graph_df['family_id']))

def run_generalization_test(
    predictions_path: Path,
    split_indices_path: Path,
    graphs_path: Path,
    output_path: Path,
    intra_family_mape: Optional[float] = None
) -> Dict[str, Any]:
    """
    Run the inter-family generalization test.
    
    1. Load predictions and split indices.
    2. Verify family disjointness between train and test.
    3. Compute inter-family MAPE on the test set.
    4. Output results to generalization_metrics.json.
    """
    # Load data
    predictions = load_json(predictions_path)
    if not predictions:
        error_report = {
            "status": "failed",
            "error": f"Predictions file not found or invalid: {predictions_path}",
            "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
        }
        save_json(error_report, output_path)
        return error_report

    split_indices = load_json(split_indices_path)
    if not split_indices:
        error_report = {
            "status": "failed",
            "error": f"Split indices file not found or invalid: {split_indices_path}",
            "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
        }
        save_json(error_report, output_path)
        return error_report

    # Split indices structure: list of dicts with 'id', 'family_id', 'split' (train/val/test)
    # We need to separate train and test based on the 'split' key if present, 
    # or assume the file contains separate lists if the structure differs.
    # Based on T017/T013d spec: "Output the final split_indices (train/val/test) used for evaluation"
    # The spec says: "list of objects: [{\"id\": \"mp-123\", \"family_id\": \"TMD_1\"},...]"
    # It implies we need to know which are train and which are test. 
    # Usually split_indices.json contains a 'split' field or is a dict {'train': [...], 'test': [...]}
    # Let's assume the standard structure from T017: a dict with keys 'train', 'val', 'test'.
    
    train_list = split_indices.get('train', [])
    test_list = split_indices.get('test', [])
    
    if not train_list or not test_list:
        # Fallback: if it's a flat list, we might not be able to distinguish. 
        # But T017 explicitly says output schema is list of objects. 
        # Let's check if the file is a dict or list.
        if isinstance(split_indices, list):
            # If it's a list, we can't distinguish train/test without a 'split' key in items.
            error_report = {
                "status": "failed",
                "error": "Split indices format invalid: expected dict with 'train' and 'test' keys.",
                "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
            }
            save_json(error_report, output_path)
            return error_report

    # Load graphs to verify family IDs
    try:
        graph_df = load_graphs_from_parquet(graphs_path)
    except FileNotFoundError as e:
        error_report = {
            "status": "failed",
            "error": str(e),
            "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
        }
        save_json(error_report, output_path)
        return error_report

    # Verify family disjointness
    if not verify_family_disjoint(train_list, test_list, graph_df):
        error_report = {
            "status": "failed",
            "error": "SC-002 Violation: Family overlap detected. Test set contains families present in training.",
            "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
        }
        save_json(error_report, output_path)
        # Halt execution as per requirement
        raise SystemExit(1)

    # Calculate Inter-Family MAPE
    # Predictions format: list of dicts with 'id', 'true', 'pred' (or similar)
    # We need to map these to family_ids to ensure we are calculating on test families.
    # Since we already verified disjointness, we can just calculate MAPE on the test set.
    
    test_ids = {item['id'] for item in test_list}
    
    y_true = []
    y_pred = []
    
    for pred in predictions:
        mat_id = pred.get('id') or pred.get('material_id')
        if mat_id in test_ids:
            true_val = pred.get('true') or pred.get('y_true')
            pred_val = pred.get('pred') or pred.get('y_pred')
            
            if true_val is not None and pred_val is not None:
                y_true.append(true_val)
                y_pred.append(pred_val)
    
    if not y_true:
        error_report = {
            "status": "failed",
            "error": "No predictions found for test set materials.",
            "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
        }
        save_json(error_report, output_path)
        return error_report

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        mape = np.nan_to_num(mape, nan=0.0)

    result = {
        "status": "success",
        "intra_family_mape": intra_family_mape,
        "inter_family_mape": float(mape),
        "test_samples": len(y_true),
        "test_families": len(set(item['family_id'] for item in test_list)),
        "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
    }
    
    save_json(result, output_path)
    return result

def main():
    parser = argparse.ArgumentParser(description="Run inter-family generalization test")
    parser.add_argument("--predictions", type=Path, required=True, help="Path to predictions.json")
    parser.add_argument("--split-indices", type=Path, required=True, help="Path to split_indices.json")
    parser.add_argument("--graphs", type=Path, required=True, help="Path to graphs_v1.parquet")
    parser.add_argument("--output", type=Path, required=True, help="Path to output generalization_metrics.json")
    parser.add_argument("--intra-mape", type=float, default=None, help="Optional intra-family MAPE to include")
    
    args = parser.parse_args()
    
    try:
        run_generalization_test(
            predictions_path=args.predictions,
            split_indices_path=args.split_indices,
            graphs_path=args.graphs,
            output_path=args.output,
            intra_family_mape=args.intra_mape
        )
    except SystemExit:
        raise
    except Exception as e:
        logger.exception("Generalization test failed unexpectedly")
        error_report = {
            "status": "failed",
            "error": str(e),
            "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
        }
        save_json(error_report, args.output)
        raise

if __name__ == "__main__":
    main()
