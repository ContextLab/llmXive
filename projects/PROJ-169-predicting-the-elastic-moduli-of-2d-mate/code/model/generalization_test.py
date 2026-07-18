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

def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], path: Path) -> None:
    """Save a dictionary to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def verify_family_disjoint(
    train_indices: List[Dict[str, Any]],
    test_indices: List[Dict[str, Any]]
) -> bool:
    """
    Verify that no family_id appears in both train and test sets.
    Returns True if disjoint, False otherwise.
    """
    train_families = set(item['family_id'] for item in train_indices)
    test_families = set(item['family_id'] for item in test_indices)
    overlap = train_families & test_families
    if overlap:
        logger.error(f"SC-002 Violation: Family overlap detected in split. Overlapping families: {overlap}")
        return False
    return True

def load_graphs_from_parquet(path: Path) -> pd.DataFrame:
    """Load graphs from a parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    return pd.read_parquet(path)

def build_family_mapping(graphs_df: pd.DataFrame) -> Dict[str, str]:
    """
    Build a mapping from material_id to family_id from the graphs dataframe.
    """
    if 'material_id' not in graphs_df.columns or 'family_id' not in graphs_df.columns:
        raise ValueError("Graphs dataframe must contain 'material_id' and 'family_id' columns.")
    return dict(zip(graphs_df['material_id'], graphs_df['family_id']))

def run_generalization_test(
    graphs_path: Path,
    split_indices_path: Path,
    predictions_path: Path,
    output_path: Path,
    intra_family_mape: Optional[float] = None
) -> Dict[str, Any]:
    """
    Run the inter-family generalization test.
    
    Args:
        graphs_path: Path to the processed graphs parquet file.
        split_indices_path: Path to the split_indices.json file.
        predictions_path: Path to the predictions.json file.
        output_path: Path to write the generalization_metrics.json output.
        intra_family_mape: Pre-computed intra-family MAPE (optional).
        
    Returns:
        A dictionary containing the metrics and status.
    """
    config = get_config()
    result = {
        "status": "success",
        "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions.",
        "intra_family_mape": intra_family_mape,
        "inter_family_mape": None,
        "error": None
    }

    try:
        # 1. Load split indices
        split_data = load_json(split_indices_path)
        train_indices = split_data.get('train', [])
        test_indices = split_data.get('test', [])

        if not train_indices or not test_indices:
            raise ValueError("Split indices must contain non-empty train and test sets.")

        # 2. Verify family disjointness (Runtime Check)
        if not verify_family_disjoint(train_indices, test_indices):
            result["status"] = "failed"
            result["error"] = "Family overlap detected in split. Halting."
            save_json(result, output_path)
            return result

        # 3. Load graphs to get family mapping
        graphs_df = load_graphs_from_parquet(graphs_path)
        family_map = build_family_mapping(graphs_df)

        # 4. Load predictions
        predictions = load_json(predictions_path)
        
        # Predictions should be a list of dicts with 'id' and 'target'/'prediction'
        # We need to match predictions to test indices
        
        test_ids = {item['id'] for item in test_indices}
        
        # Filter predictions for test set only
        test_predictions = [p for p in predictions if p.get('id') in test_ids]
        
        if not test_predictions:
            raise ValueError("No predictions found for the test set.")

        # 5. Calculate Inter-Family MAPE
        # We assume predictions have 'target' (y_true) and 'prediction' (y_pred)
        y_true = []
        y_pred = []
        
        for p in test_predictions:
            if 'target' in p and 'prediction' in p:
                y_true.append(p['target'])
                y_pred.append(p['prediction'])
            else:
                # Fallback if keys are different, e.g., 'y_true', 'y_pred'
                if 'y_true' in p and 'y_pred' in p:
                    y_true.append(p['y_true'])
                    y_pred.append(p['y_pred'])
                else:
                    logger.warning(f"Skipping prediction entry missing target/prediction keys: {p}")
                    
        if not y_true:
            raise ValueError("Could not extract valid targets and predictions for MAPE calculation.")

        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        
        # Avoid division by zero
        epsilon = 1e-8
        mape = np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + epsilon))) * 100.0
        
        result["inter_family_mape"] = float(mape)
        result["test_size"] = len(y_true)
        result["train_families_count"] = len(set(item['family_id'] for item in train_indices))
        result["test_families_count"] = len(set(item['family_id'] for item in test_indices))

        logger.info(f"Inter-family MAPE calculated: {mape:.2f}%")

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        logger.error(f"Generalization test failed: {e}")

    save_json(result, output_path)
    return result

def main():
    parser = argparse.ArgumentParser(description="Run inter-family generalization test.")
    parser.add_argument("--graphs", type=str, required=True, help="Path to graphs_v1.parquet")
    parser.add_argument("--split-indices", type=str, required=True, help="Path to split_indices.json")
    parser.add_argument("--predictions", type=str, required=True, help="Path to predictions.json")
    parser.add_argument("--output", type=str, required=True, help="Path to output generalization_metrics.json")
    parser.add_argument("--intra-family-mape", type=float, default=None, help="Pre-computed intra-family MAPE")
    
    args = parser.parse_args()

    graphs_path = Path(args.graphs)
    split_indices_path = Path(args.split_indices)
    predictions_path = Path(args.predictions)
    output_path = Path(args.output)

    run_generalization_test(
        graphs_path=graphs_path,
        split_indices_path=split_indices_path,
        predictions_path=predictions_path,
        output_path=output_path,
        intra_family_mape=args.intra_family_mape
    )

    logger.info(f"Generalization test completed. Results saved to {output_path}")

if __name__ == "__main__":
    main()
