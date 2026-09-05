"""
Simulator module for AgenticSTS bounded-memory testbed.
Implements dynamic layer selection, token budgeting, and detailed logging.
"""
import os
import json
import logging
import pickle
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MIN_CONTEXT = 256  # tokens
DEFAULT_MAX_BUDGET = 4096  # tokens
MODEL_PATH = Path("models/layer_utility_classifier.pkl")
PROCESSED_DIR = Path("data/processed")
RAW_DIR = Path("data/raw")

def estimate_layer_tokens(layer_data: Dict[str, Any]) -> int:
    """
    Estimate token count for a given layer data.
    Simple heuristic: count characters / 4 (approx tokens).
    """
    if not layer_data:
        return 0
    # Convert to string if not already
    layer_str = json.dumps(layer_data) if not isinstance(layer_data, str) else layer_data
    return len(layer_str) // 4

def calculate_total_tokens(layers: List[Dict[str, Any]]) -> int:
    """Calculate total tokens for a list of layers."""
    return sum(estimate_layer_tokens(layer) for layer in layers)

def prune_layers_for_budget(
    layers: List[Dict[str, Any]],
    target_budget: int,
    utility_scores: Optional[List[float]] = None
) -> Tuple[List[Dict[str, Any]], List[str], str]:
    """
    Prune layers to fit within token budget.
    Returns: (pruned_layers, layers_pruned, pruning_reason)
    """
    current_tokens = calculate_total_tokens(layers)
    if current_tokens <= target_budget:
        return layers, [], "No pruning needed"

    if utility_scores and len(utility_scores) == len(layers):
        # Sort by utility (lowest first) to prune least useful
        indexed_layers = list(enumerate(layers))
        indexed_scores = list(enumerate(utility_scores))
        
        # Sort indices by score (ascending)
        sorted_indices = sorted(
            range(len(indexed_scores)),
            key=lambda i: indexed_scores[i]
        )
        
        pruned = []
        pruned_indices = []
        remaining_layers = layers.copy()
        remaining_tokens = current_tokens
        
        for idx in sorted_indices:
            if remaining_tokens <= target_budget:
                break
            layer_to_remove = remaining_layers[idx]
            remaining_tokens -= estimate_layer_tokens(layer_to_remove)
            pruned.append(layer_to_remove)
            pruned_indices.append(idx)
        
        # Reconstruct remaining layers
        final_layers = [
            layer for i, layer in enumerate(layers) if i not in pruned_indices
        ]
        
        return final_layers, [f"layer_{i}" for i in pruned_indices], "Token budget exceeded"
    else:
        # Fallback: prune from end
        pruned = []
        remaining = layers.copy()
        while calculate_total_tokens(remaining) > target_budget and remaining:
            removed = remaining.pop()
            pruned.append(removed)
        
        return remaining, [f"layer_{i}" for i in range(len(layers) - len(remaining), len(layers))], "Token budget exceeded"

def enforce_minimum_context(
    layers: List[Dict[str, Any]],
    min_context: int = DEFAULT_MIN_CONTEXT
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Ensure minimum context floor is met.
    If context is below min_context, append objective layer.
    Returns: (layers, was_floor_applied)
    """
    current_tokens = calculate_total_tokens(layers)
    if current_tokens >= min_context:
        return layers, False
    
    # Add objective layer
    objective_layer = {
        "layer_type": "objective",
        "content": "Current Objective: Complete the task efficiently",
        "priority": "high"
    }
    layers.append(objective_layer)
    return layers, True

def predict_layer_utility(
    trajectory_data: Dict[str, Any],
    model_path: Path = MODEL_PATH
) -> List[float]:
    """
    Predict utility scores for layers using trained model.
    Returns list of utility scores for each layer.
    """
    if not model_path.exists():
        logger.warning(f"Model not found at {model_path}, using heuristic fallback")
        # Heuristic: uniform utility
        n_layers = len(trajectory_data.get("layers", []))
        return [1.0 / n_layers] * n_layers if n_layers > 0 else []
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Extract features (simplified - in real implementation would use proper feature extraction)
        features = []
        for layer in trajectory_data.get("layers", []):
            # Simple feature: layer complexity
            feature = len(json.dumps(layer)) / 1000.0
            features.append([feature])
        
        if not features:
            return []
        
        predictions = model.predict_proba(features)[:, 1] if hasattr(model, 'predict_proba') else model.predict(features)
        return predictions.tolist()
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        n_layers = len(trajectory_data.get("layers", []))
        return [0.5] * n_layers if n_layers > 0 else []

def load_raw_trajectory(trajectory_id: str) -> Optional[Dict[str, Any]]:
    """Load raw trajectory data from disk."""
    # Look for trajectory in various formats
    for ext in ['.json', '.jsonl']:
        filepath = RAW_DIR / f"{trajectory_id}{ext}"
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    if ext == '.jsonl':
                        for line in f:
                            data = json.loads(line)
                            if data.get("trajectory_id") == trajectory_id:
                                return data
                    else:
                        return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {filepath}: {e}")
    
    # Try loading from aggregated file
    aggregated_path = RAW_DIR / "agenticsts_trajectories.jsonl"
    if aggregated_path.exists():
        try:
            with open(aggregated_path, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("trajectory_id") == trajectory_id:
                        return data
        except Exception as e:
            logger.error(f"Error loading aggregated trajectories: {e}")
    
    return None

def run_dynamic_simulation(
    trajectory_id: str,
    model_path: Path = MODEL_PATH,
    max_budget: int = DEFAULT_MAX_BUDGET,
    min_context: int = DEFAULT_MIN_CONTEXT
) -> Dict[str, Any]:
    """
    Run dynamic simulation for a trajectory with token budget logging.
    Returns detailed simulation results including token budget information.
    """
    trajectory_data = load_raw_trajectory(trajectory_id)
    if not trajectory_data:
        logger.error(f"Trajectory {trajectory_id} not found")
        return {"error": f"Trajectory {trajectory_id} not found"}
    
    layers = trajectory_data.get("layers", [])
    if not layers:
        return {"error": "No layers in trajectory"}
    
    # Step 1: Enforce minimum context
    layers, floor_applied = enforce_minimum_context(layers, min_context)
    
    # Step 2: Predict utility
    utility_scores = predict_layer_utility(trajectory_data, model_path)
    
    # Step 3: Select top-k layers based on utility
    if utility_scores:
        # Sort layers by utility (descending)
        indexed_layers = list(enumerate(layers))
        indexed_scores = list(enumerate(utility_scores))
        sorted_indices = sorted(
            range(len(indexed_scores)),
            key=lambda i: indexed_scores[i],
            reverse=True
        )
        selected_indices = sorted_indices[:min(5, len(sorted_indices))]  # Top 5
        selected_layers = [layers[i] for i in selected_indices]
    else:
        selected_layers = layers[:5]
    
    # Step 4: Calculate initial tokens
    initial_tokens = calculate_total_tokens(selected_layers)
    
    # Step 5: Prune if necessary
    final_layers, layers_pruned, pruning_reason = prune_layers_for_budget(
        selected_layers, max_budget, utility_scores
    )
    final_tokens = calculate_total_tokens(final_layers)
    
    # Build detailed token budget log
    token_budget_log = {
        "trajectory_id": trajectory_id,
        "initial_tokens": initial_tokens,
        "selected_layers": [f"layer_{i}" for i in range(len(selected_layers))],
        "final_tokens": final_tokens,
        "layers_pruned": layers_pruned,
        "pruning_reason": pruning_reason,
        "floor_applied": floor_applied,
        "utility_scores": utility_scores,
        "final_layer_count": len(final_layers)
    }
    
    return token_budget_log

def run_baseline_simulation(
    trajectory_id: str,
    mode: str = "static",
    max_budget: int = DEFAULT_MAX_BUDGET
) -> Dict[str, Any]:
    """
    Run baseline simulation (static or random).
    """
    trajectory_data = load_raw_trajectory(trajectory_id)
    if not trajectory_data:
        return {"error": f"Trajectory {trajectory_id} not found"}
    
    layers = trajectory_data.get("layers", [])
    if not layers:
        return {"error": "No layers in trajectory"}
    
    if mode == "static":
        # Use all layers
        selected_layers = layers
    elif mode == "random":
        import random
        k = min(2, len(layers))
        selected_layers = random.sample(layers, k)
    else:
        selected_layers = layers[:5]
    
    tokens = calculate_total_tokens(selected_layers)
    
    return {
        "trajectory_id": trajectory_id,
        "mode": mode,
        "tokens": tokens,
        "layer_count": len(selected_layers)
    }

def generate_token_budget_detailed_csv(
    trajectory_ids: List[str],
    output_path: Path = PROCESSED_DIR / "token_budget_detailed.csv",
    mode: str = "dynamic",
    model_path: Path = MODEL_PATH,
    max_budget: int = DEFAULT_MAX_BUDGET,
    min_context: int = DEFAULT_MIN_CONTEXT
) -> Path:
    """
    Generate detailed token budget CSV for multiple trajectories.
    This is the main function for T056.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = []
    for traj_id in trajectory_ids:
        if mode == "dynamic":
            result = run_dynamic_simulation(
                traj_id, model_path, max_budget, min_context
            )
        else:
            result = run_baseline_simulation(traj_id, mode, max_budget)
        
        if "error" in result:
            logger.warning(f"Skipping {traj_id}: {result['error']}")
            continue
        
        results.append(result)
    
    # Write to CSV
    if results:
        fieldnames = [
            "trajectory_id", 
            "initial_tokens", 
            "selected_layers", 
            "final_tokens", 
            "layers_pruned", 
            "pruning_reason"
        ]
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                # Format selected_layers and layers_pruned as comma-separated strings
                row = {
                    "trajectory_id": result.get("trajectory_id"),
                    "initial_tokens": result.get("initial_tokens", 0),
                    "selected_layers": ",".join(result.get("selected_layers", [])),
                    "final_tokens": result.get("final_tokens", 0),
                    "layers_pruned": ",".join(result.get("layers_pruned", [])),
                    "pruning_reason": result.get("pruning_reason", "None")
                }
                writer.writerow(row)
        
        logger.info(f"Token budget detailed CSV written to {output_path}")
        logger.info(f"Processed {len(results)} trajectories")
    
    return output_path

def main():
    """Main entry point for simulator module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simulator for AgenticSTS")
    parser.add_argument("--mode", choices=["dynamic", "static", "random"], default="dynamic")
    parser.add_argument("--trajectories", nargs="+", help="Trajectory IDs to process")
    parser.add_argument("--output", default=str(PROCESSED_DIR / "token_budget_detailed.csv"))
    parser.add_argument("--model", default=str(MODEL_PATH))
    parser.add_argument("--max-budget", type=int, default=DEFAULT_MAX_BUDGET)
    parser.add_argument("--min-context", type=int, default=DEFAULT_MIN_CONTEXT)
    
    args = parser.parse_args()
    
    if not args.trajectories:
        # Load test set if no trajectories specified
        test_set_path = PROCESSED_DIR / "test_set.csv"
        if test_set_path.exists():
            import pandas as pd
            df = pd.read_csv(test_set_path)
            trajectory_ids = df["trajectory_id"].tolist()
        else:
            logger.error("No trajectories specified and test_set.csv not found")
            return 1
    else:
        trajectory_ids = args.trajectories
    
    generate_token_budget_detailed_csv(
        trajectory_ids=trajectory_ids,
        output_path=Path(args.output),
        mode=args.mode,
        model_path=Path(args.model),
        max_budget=args.max_budget,
        min_context=args.min_context
    )
    
    return 0

if __name__ == "__main__":
    exit(main())
