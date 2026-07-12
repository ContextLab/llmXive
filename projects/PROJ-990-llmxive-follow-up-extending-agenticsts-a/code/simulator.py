import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np
import pandas as pd

from config import load_config_from_file, ensure_directories
from classifier import load_model
from entropy import calculate_shannon_entropy, extract_move_distribution

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Token Budget Helpers (from T015/T016 logic) ---

def estimate_layer_tokens(layer_data: Dict[str, Any]) -> int:
    """
    Estimate token count for a specific layer context.
    Heuristic: 1 token ~ 4 characters + overhead for JSON structure.
    """
    if not layer_data:
        return 0
    # Simple heuristic: sum of string lengths + structural overhead
    content_str = json.dumps(layer_data)
    return len(content_str) // 4 + 50  # 50 overhead per layer block

def calculate_total_tokens(layer_list: List[Dict[str, Any]]) -> int:
    """Calculate total tokens for a list of layers."""
    return sum(estimate_layer_tokens(layer) for layer in layer_list)

def prune_layers_for_budget(layer_list: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
    """
    Prune least useful layers to fit within max_tokens.
    Assumes layers have a 'utility_score' or similar metric if available.
    If not, prunes from the end (oldest/least relevant in some contexts).
    """
    current_tokens = calculate_total_tokens(layer_list)
    if current_tokens <= max_tokens:
        return layer_list

    # Sort by utility descending if available, else keep order
    # For this implementation, we assume we drop from the front (oldest)
    # or based on a 'utility_score' key if present.
    # Here we implement a greedy drop: remove lowest utility first.
    scored_layers = []
    for i, layer in enumerate(layer_list):
        score = layer.get('utility_score', 0.0)
        scored_layers.append((i, score, layer))

    # Sort by score ascending (lowest utility first)
    scored_layers.sort(key=lambda x: x[1])

    pruned = []
    kept_indices = set()
    current_tokens = 0

    # We need to keep the highest utility layers that fit
    # Reverse sort to pick best first
    scored_layers.sort(key=lambda x: x[1], reverse=True)

    final_layers = []
    for idx, score, layer in scored_layers:
        est_tokens = estimate_layer_tokens(layer)
        if current_tokens + est_tokens <= max_tokens:
            final_layers.append(layer)
            current_tokens += est_tokens
        else:
            # Can't fit this one, skip
            pass
    
    # Return in original order? Or just the subset. 
    # Usually order matters for context. Let's preserve original relative order of kept items.
    # Re-collect based on the best set
    best_indices = {item[0] for item in scored_layers if item[2] in final_layers}
    result = [layer for i, layer in enumerate(layer_list) if i in best_indices]
    
    logger.warning(f"Pruned layers to fit budget. Original: {len(layer_list)}, Kept: {len(result)}, Tokens: {current_tokens}/{max_tokens}")
    return result

def enforce_minimum_context(layer_list: List[Dict[str, Any]], min_tokens: int) -> List[Dict[str, Any]]:
    """
    Ensure a minimum context floor. If total tokens < min_tokens, 
    we might need to pad or retrieve more (not implemented here, just log).
    """
    current_tokens = calculate_total_tokens(layer_list)
    if current_tokens < min_tokens:
        logger.warning(f"Context below minimum floor ({current_tokens} < {min_tokens}). "
                       "Retrieving full set or padding logic not implemented in this baseline.")
        # In a real scenario, we might fetch more history. 
        # For now, we just proceed but log.
    return layer_list

# --- Simulation Logic ---

def run_dynamic_simulation(
    trajectory: Dict[str, Any], 
    model_path: Path, 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run simulation with dynamic layer selection (T015 logic).
    Uses classifier to pick top-k layers based on entropy.
    """
    # Load model
    try:
        model = load_model(model_path)
    except FileNotFoundError:
        logger.error(f"Model not found at {model_path}. Skipping dynamic simulation.")
        return {"status": "error", "reason": "model_missing"}

    # Extract per-turn metrics (simplified for this context)
    turns = trajectory.get('turns', [])
    selected_layers = []
    total_tokens = 0
    
    for turn in turns:
        # Calculate entropy for this turn
        moves = turn.get('legal_moves', [])
        entropy = calculate_shannon_entropy(moves)
        
        # Predict top-k layers
        # Feature vector: [entropy, health, threat, deck_size]
        features = [
            entropy if not np.isnan(entropy) else 0.0,
            turn.get('health', 0),
            turn.get('threat', 0),
            turn.get('deck_size', 0)
        ]
        
        # Predict k (number of layers to retrieve)
        # Assuming model predicts 'k' or a utility score for each layer
        # For simplicity, assume model returns a predicted 'k' value
        pred_k = int(model.predict([features])[0])
        pred_k = min(pred_k, config.get('MAX_LAYERS', 10))
        
        # Select top-k layers from available history (simplified)
        # In reality, we'd query a vector store or index
        available_history = trajectory.get('history', [])
        selected = available_history[:pred_k]
        
        # Enforce budget
        if calculate_total_tokens(selected) > config.get('TOKEN_BUDGET', 4096):
            selected = prune_layers_for_budget(selected, config.get('TOKEN_BUDGET', 4096))
        
        selected_layers.append({
            "turn": turn.get('turn_id'),
            "entropy": entropy,
            "selected_layers_count": len(selected),
            "tokens": calculate_total_tokens(selected)
        })
        
        total_tokens += calculate_total_tokens(selected)

    return {
        "condition": "dynamic",
        "trajectory_id": trajectory.get('id'),
        "selected_layers_summary": selected_layers,
        "total_tokens": total_tokens,
        "status": "success"
    }

def run_baseline_simulation(
    trajectory: Dict[str, Any], 
    baseline_type: str, 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run simulation for baselines: 'static_all_layers' or 'no_store_random'.
    
    T019: Static All-Layers - retrieves every layer up to a limit.
    T020: No-Store Random - randomly selects layers without memory of past choices, 
          effectively simulating an agent with no retrieval strategy.
    """
    turns = trajectory.get('turns', [])
    history = trajectory.get('history', [])
    results = []
    total_tokens = 0
    win_rate = 0.0 # Placeholder, real logic depends on simulation outcome

    if baseline_type == "static_all_layers":
        # T019 Logic: Use all available layers (capped by budget if necessary)
        for turn in turns:
            # Use full history
            layers_to_use = history
            if calculate_total_tokens(layers_to_use) > config.get('TOKEN_BUDGET', 4096):
                layers_to_use = prune_layers_for_budget(layers_to_use, config.get('TOKEN_BUDGET', 4096))
            
            results.append({
                "turn": turn.get('turn_id'),
                "method": "static_all",
                "layers_count": len(layers_to_use),
                "tokens": calculate_total_tokens(layers_to_use)
            })
            total_tokens += calculate_total_tokens(layers_to_use)

    elif baseline_type == "no_store_random":
        # T020 Logic: "No-Store Random"
        # At each turn, randomly select a subset of layers (k) from the full history.
        # "No-Store" implies no persistent memory of what was retrieved previously,
        # just a fresh random draw from the available pool at each step.
        # This simulates an agent that doesn't learn a retrieval policy.
        
        for turn in turns:
            # Randomly determine k (e.g., 1 to max_layers)
            max_k = min(len(history), config.get('MAX_LAYERS', 10))
            if max_k == 0:
                selected = []
            else:
                k = np.random.randint(1, max_k + 1)
                # Random sample without replacement
                selected = np.random.choice(history, size=k, replace=False).tolist()
            
            # Enforce budget
            if calculate_total_tokens(selected) > config.get('TOKEN_BUDGET', 4096):
                selected = prune_layers_for_budget(selected, config.get('TOKEN_BUDGET', 4096))
            
            results.append({
                "turn": turn.get('turn_id'),
                "method": "no_store_random",
                "layers_count": len(selected),
                "tokens": calculate_total_tokens(selected)
            })
            total_tokens += calculate_total_tokens(selected)
    
    else:
        raise ValueError(f"Unknown baseline type: {baseline_type}")

    return {
        "condition": baseline_type,
        "trajectory_id": trajectory.get('id'),
        "turn_details": results,
        "total_tokens": total_tokens,
        "status": "success"
    }

def main():
    """
    Entry point for baseline simulations (T019, T020).
    Loads trajectories, runs baselines, and saves results.
    """
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        # Fallback to defaults if config file missing
        config = {
            "TOKEN_BUDGET": 4096,
            "MAX_LAYERS": 10,
            "DATA_PATH": "data/raw/trajectories.csv",
            "OUTPUT_PATH": "data/processed/baseline_results.json"
        }
    else:
        config = load_config_from_file(config_path)

    ensure_directories(config)

    data_path = Path(config.get("DATA_PATH", "data/raw/trajectories.csv"))
    output_path = Path(config.get("OUTPUT_PATH", "data/processed/baseline_results.json"))

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return

    # Load trajectories
    df = pd.read_csv(data_path)
    trajectories = df.to_dict(orient='records')

    logger.info(f"Loaded {len(trajectories)} trajectories.")

    all_results = []

    # Run T020: No-Store Random Baseline
    logger.info("Running No-Store Random Baseline (T020)...")
    for traj in trajectories:
        result = run_baseline_simulation(traj, "no_store_random", config)
        all_results.append(result)

    # Run T019: Static All-Layers Baseline (if needed for comparison)
    logger.info("Running Static All-Layers Baseline (T019)...")
    for traj in trajectories:
        result = run_baseline_simulation(traj, "static_all_layers", config)
        all_results.append(result)

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Baseline simulation results saved to {output_path}")

if __name__ == "__main__":
    main()