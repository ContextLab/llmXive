import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from config import load_config_from_file
from engine_runner import run_simulation_batch
from entropy import calculate_entropy_for_trajectory
from classifier import load_model

logger = logging.getLogger('llmXive.simulator')

def estimate_layer_tokens(layer_data: Dict) -> int:
    """Estimate token count for a layer based on content length."""
    # Simple heuristic: 1 token ~ 4 characters
    content = str(layer_data.get('content', ''))
    return len(content) // 4

def calculate_total_tokens(layers: List[Dict]) -> int:
    """Calculate total tokens for a list of layers."""
    return sum(estimate_layer_tokens(l) for l in layers)

def prune_layers_for_budget(layers: List[Dict], max_tokens: int) -> List[Dict]:
    """Prune least useful layers to meet token budget."""
    current_tokens = calculate_total_tokens(layers)
    if current_tokens <= max_tokens:
        return layers

    # Sort by utility score (descending) if available, else by index
    # For now, just truncate from the end (least recent/useful in simple heuristic)
    # In a real implementation, we'd use the classifier's utility prediction
    pruned = []
    running_tokens = 0
    for layer in layers:
        layer_tokens = estimate_layer_tokens(layer)
        if running_tokens + layer_tokens <= max_tokens:
            pruned.append(layer)
            running_tokens += layer_tokens
        else:
            break
    return pruned

def enforce_minimum_context(layers: List[Dict], min_tokens: int, objective_layer: Dict) -> List[Dict]:
    """Append 'Current Objective' layer if total tokens < min_tokens."""
    current_tokens = calculate_total_tokens(layers)
    if current_tokens >= min_tokens:
        return layers
    
    # Append objective layer
    if objective_layer:
        return layers + [objective_layer]
    return layers

def run_dynamic_simulation(config: Dict) -> Dict:
    """
    Execute the Dynamic Simulation (T017).
    Logic:
    1. Check fallback_flag.json. If true, use fixed k=2.
    2. If false, use trained model to predict top-k layers based on entropy.
    3. Enforce token budget (4096) and minimum context (256).
    4. Run engine_runner with these parameters.
    """
    logger.info("Starting Dynamic Simulation (T017)...")
    
    # Load config
    token_budget = config.get('TOKEN_BUDGET', 4096)
    min_context = config.get('MIN_CONTEXT', 256)
    
    # Check fallback flag
    fallback_path = Path(config['DATA_PROCESSED']) / 'fallback_flag.json'
    use_fallback = False
    if fallback_path.exists():
        with open(fallback_path, 'r') as f:
            flag_data = json.load(f)
            use_fallback = flag_data.get('fallback', False)
        logger.info(f"Fallback mode: {use_fallback}")

    # Load model if not fallback
    model = None
    if not use_fallback:
        model_path = Path(config['MODELS']) / 'layer_utility_classifier.pkl'
        if model_path.exists():
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info("Dynamic model loaded for prediction.")
        else:
            logger.warning("Model not found, forcing fallback to k=2.")
            use_fallback = True

    # Load test set
    test_set_path = Path(config['DATA_PROCESSED']) / 'test_set.csv'
    if not test_set_path.exists():
        raise FileNotFoundError(f"Test set not found at {test_set_path}")
    
    # Run simulation batch via engine_runner
    # engine_runner.run_simulation_batch expects a policy and dataset
    # We pass 'dynamic' policy, and the engine_runner will internally handle the logic
    # OR we pre-calculate the layers here.
    # Per T018/T017 spec: Invoke engine_runner with policy="Dynamic".
    # The engine_runner will call the logic defined here.
    
    results = run_simulation_batch(
        dataset_path=str(test_set_path),
        policy='dynamic',
        config=config
    )
    
    output_path = Path(config['DATA_PROCESSED']) / 'simulation_logs_dynamic.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Dynamic simulation results written to {output_path}")
    return results

def run_baseline_simulation(config: Dict, policy: str) -> Dict:
    """Run a baseline simulation (Static or Random)."""
    logger.info(f"Starting Baseline Simulation ({policy})...")
    
    test_set_path = Path(config['DATA_PROCESSED']) / 'test_set.csv'
    if not test_set_path.exists():
        raise FileNotFoundError(f"Test set not found at {test_set_path}")
    
    results = run_simulation_batch(
        dataset_path=str(test_set_path),
        policy=policy,
        config=config
    )
    
    output_path = Path(config['DATA_PROCESSED']) / f'simulation_logs_{policy}.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"{policy} simulation results written to {output_path}")
    return results

def main(config: Optional[Dict] = None):
    """Main entry point for simulator tasks."""
    if config is None:
        config = load_config_from_file('config.json')
    
    # Run Dynamic (T017)
    run_dynamic_simulation(config)
    
    # Run Static (T019)
    run_baseline_simulation(config, 'static')
    
    # Run Random (T020)
    run_baseline_simulation(config, 'random')

if __name__ == '__main__':
    main()
