"""
Predict barrier heights for the held-out test set using the trained ensemble.

This script loads the 5-fold LLSO splits, identifies the test samples,
loads the trained SchNet ensemble models, generates predictions, and
computes the error residuals (ML - DFT).

Output: code/data/processed/residuals.parquet
"""
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Batch

# Project root resolution
ROOT = Path(__file__).resolve().parent.parent.parent
if ROOT.name == "src":
    ROOT = ROOT.parent
if ROOT.name == "code":
    ROOT = ROOT.parent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT / "logs" / "predict.log", mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Import local modules (assuming code/src is in sys.path or relative import structure)
# We need to ensure the path is set up correctly for imports
sys.path.insert(0, str(ROOT))
from code.src.models.schnet import SchNet
from code.src.utils.config import config

def get_project_root() -> Path:
    """Return the project root directory."""
    return ROOT

def load_splits(splits_path: Path) -> Dict[str, List[List[int]]]:
    """Load the LLSO splits JSON."""
    logger.info(f"Loading splits from {splits_path}")
    with open(splits_path, "r") as f:
        splits = json.load(f)
    return splits

def load_graphs_for_prediction(graphs_path: Path, indices: List[int]) -> Batch:
    """
    Load specific graphs from the parquet file based on indices.
    Returns a PyTorch Geometric Batch object.
    """
    logger.info(f"Loading {len(indices)} graphs for prediction from {graphs_path}")
    df = pd.read_parquet(graphs_path)
    
    # Filter dataframe by indices
    # Assuming 'sample_id' or index matches the split indices
    if 'sample_id' in df.columns:
        # If sample_id is string, convert indices to string if necessary
        # But typically splits use integer indices corresponding to df index
        subset_df = df.iloc[indices]
    else:
        subset_df = df.iloc[indices]

    if subset_df.empty:
        raise ValueError(f"No graphs found for indices {indices[:5]}...")

    # Reconstruct Batch from dataframe rows
    # This assumes the dataframe contains serialized graph data or we have a loader
    # Based on typical pipeline, graphs.parquet usually stores edge_index, x, y, etc.
    # Or it stores a 'graph' column with pickle data.
    # Let's assume a standard structure: x, edge_index, edge_attr, y (barrier), sample_id
    
    # We need to reconstruct PyG Data objects
    graphs = []
    for _, row in subset_df.iterrows():
        # Handle potential serialization formats
        # Case 1: Columns are direct tensors (unlikely in parquet without custom engine)
        # Case 2: Columns are lists/arrays that need conversion
        # Case 3: A 'graph' column with pickled objects (most robust for complex graphs)
        
        if 'graph' in row.index and pd.notna(row['graph']):
            # Pickled graph
            import pickle
            import io
            # If it's bytes, load directly. If it's a string representation, need to eval/loads
            if isinstance(row['graph'], bytes):
                data = pickle.loads(row['graph'])
            else:
                # Fallback for stringified pickle
                data = pickle.loads(io.BytesIO(row['graph']).read())
        else:
            # Reconstruct from columns (assuming standard columns exist)
            # This part is highly dependent on how T017b saved the data.
            # Assuming standard columns: 'x', 'edge_index', 'edge_attr', 'y', 'sample_id'
            x = torch.tensor(row['x'], dtype=torch.float) if isinstance(row['x'], list) else row['x']
            edge_index = torch.tensor(row['edge_index'], dtype=torch.long) if isinstance(row['edge_index'], list) else row['edge_index']
            edge_attr = torch.tensor(row['edge_attr'], dtype=torch.float) if isinstance(row['edge_attr'], list) else row['edge_attr']
            y = torch.tensor([row['y']], dtype=torch.float) if isinstance(row['y'], (int, float)) else row['y']
            
            # Create Data object
            from torch_geometric.data import Data
            data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
            # Add metadata if present
            if 'sample_id' in row.index:
                data.sample_id = str(row['sample_id'])
            if 'ligand_class' in row.index:
                data.ligand_class = row['ligand_class']
            if 'metal_center' in row.index:
                data.metal_center = row['metal_center']

        graphs.append(data)

    if not graphs:
        raise ValueError("No graphs reconstructed.")

    batch = Batch.from_data_list(graphs)
    return batch

def load_ensemble_models(models_dir: Path, num_models: int = 5) -> List[SchNet]:
    """Load all trained SchNet models from the directory."""
    models = []
    for i in range(num_models):
        model_path = models_dir / f"seed_{i}.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
        
        logger.info(f"Loading model {i} from {model_path}")
        model = SchNet() # Assuming default constructor matches training config
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()
        models.append(model)
    
    return models

def predict_batch(batch: Batch, models: List[SchNet]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run inference on a batch using all ensemble models.
    Returns: (mean_predictions, variance_predictions)
    """
    predictions = []
    
    with torch.no_grad():
        for model in models:
            output = model(batch)
            # output shape: [num_graphs] or [num_graphs, 1]
            if output.dim() > 1:
                output = output.squeeze(-1)
            predictions.append(output.cpu().numpy())
    
    predictions = np.stack(predictions, axis=-1) # [num_samples, num_models]
    mean_preds = np.mean(predictions, axis=1)
    var_preds = np.var(predictions, axis=1)
    
    return mean_preds, var_preds

def extract_test_indices(splits: Dict[str, List[List[int]]]) -> List[int]:
    """Flatten the test indices from the 5-fold splits."""
    # The splits format is {"train": [...], "val": [...], "test": [...]}
    # where each value is a list of 5 lists (one per fold).
    # We need to aggregate all test indices across all 5 folds?
    # Or process fold by fold? The task says "held-out test set".
    # Usually, we evaluate on the union of all test sets if we want a single metric,
    # OR we evaluate fold-by-fold.
    # Given T025 says "held-out test set" (singular) and T027a aggregates,
    # we will collect all unique test indices from the 5 folds.
    
    test_indices = []
    for fold_test in splits["test"]:
        test_indices.extend(fold_test)
    
    # Remove duplicates just in case, though LLSO should be disjoint
    test_indices = sorted(list(set(test_indices)))
    logger.info(f"Total unique test samples: {len(test_indices)}")
    return test_indices

def run_prediction() -> None:
    """Main execution function for T025."""
    # Paths
    splits_path = get_project_root() / "code" / "data" / "processed" / "splits.json"
    graphs_path = get_project_root() / "code" / "data" / "processed" / "graphs.parquet"
    models_dir = get_project_root() / "code" / "data" / "processed" / "models"
    output_path = get_project_root() / "code" / "data" / "processed" / "residuals.parquet"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load Splits
    splits = load_splits(splits_path)
    test_indices = extract_test_indices(splits)

    if not test_indices:
        logger.error("No test indices found in splits.")
        sys.exit(1)

    # 2. Load Graphs for test set
    # We need to load the full graph data to extract metadata (ligand_class, metal_center)
    # and the graph structure for inference.
    try:
        test_batch = load_graphs_for_prediction(graphs_path, test_indices)
    except Exception as e:
        logger.error(f"Failed to load graphs: {e}")
        sys.exit(1)

    # 3. Load Models
    try:
        models = load_ensemble_models(models_dir)
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        sys.exit(1)

    # 4. Generate Predictions
    logger.info("Running inference...")
    start_time = time.time()
    mean_preds, var_preds = predict_batch(test_batch, models)
    inference_time = time.time() - start_time
    logger.info(f"Inference completed in {inference_time:.2f}s for {len(test_indices)} samples.")

    # 5. Prepare Output Data
    # Load metadata from the original dataframe to match indices
    df = pd.read_parquet(graphs_path)
    # Filter for test indices
    test_df = df.iloc[test_indices].copy()
    
    # Ensure alignment: test_df index might not be sequential 0..N, but matches test_indices
    # We need to construct the result dataframe row by row or ensure index alignment
    
    results_data = {
        "sample_id": [],
        "error_ml_dft": [],
        "ligand_class": [],
        "metal_center": [],
        "predicted_barrier": [],
        "dft_barrier": [],
        "ensemble_variance": []
    }

    # Iterate through the test samples (aligned by position in test_indices)
    for i, idx in enumerate(test_indices):
        # Get row from original df
        row = df.iloc[idx]
        
        sample_id = str(row.get('sample_id', idx))
        ligand_class = row.get('ligand_class', 'Unknown')
        metal_center = row.get('metal_center', 'Unknown')
        dft_barrier = float(row['y']) # Assuming 'y' is the DFT barrier height
        
        pred_barrier = float(mean_preds[i])
        error = pred_barrier - dft_barrier
        variance = float(var_preds[i])

        results_data["sample_id"].append(sample_id)
        results_data["error_ml_dft"].append(error)
        results_data["ligand_class"].append(ligand_class)
        results_data["metal_center"].append(metal_center)
        results_data["predicted_barrier"].append(pred_barrier)
        results_data["dft_barrier"].append(dft_barrier)
        results_data["ensemble_variance"].append(variance)

    results_df = pd.DataFrame(results_data)

    # 6. Save Output
    logger.info(f"Saving residuals to {output_path}")
    results_df.to_parquet(output_path, index=False)
    
    logger.info("T025 completed successfully.")
    print(f"Output written to: {output_path}")
    print(f"Rows: {len(results_df)}")
    print(f"Columns: {list(results_df.columns)}")
    print(f"Sample Error Stats: Mean={results_df['error_ml_dft'].mean():.4f}, Std={results_df['error_ml_dft'].std():.4f}")

def main():
    run_prediction()

if __name__ == "__main__":
    main()