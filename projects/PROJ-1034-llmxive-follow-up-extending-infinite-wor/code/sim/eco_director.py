import yaml
import os
from typing import Any, Dict, Tuple, Optional, List
import numpy as np
import time
from config import set_seed
from sim.health_monitor import HealthMonitor

def load_config(config_path: str) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    required_keys = ['grid_size', 'steps', 'seed']
    for key in required_keys:
        if key not in config:
            return False
    return True

def eco_director_step(state: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """
    Performs one step of the CA simulation.
    Implements basic cellular automaton logic with configurable parameters.
    """
    grid_size = state.shape[0]
    new_state = np.zeros_like(state)
    
    # Simple rule: cell is alive if neighbors sum to 2 or 3 (Game of Life style)
    # This is a placeholder for the actual complex CA logic
    for i in range(grid_size):
        for j in range(grid_size):
            neighbors = 0
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    ni, nj = (i + dx) % grid_size, (j + dy) % grid_size
                    neighbors += state[ni, nj]
            
            if state[i, j] == 1:
                new_state[i, j] = 1 if neighbors in [2, 3] else 0
            else:
                new_state[i, j] = 1 if neighbors == 3 else 0
    
    return new_state

def run_simulation(config: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs the full simulation loop.
    Returns a summary of results including metrics.
    """
    set_seed(config['seed'])
    grid_size = config['grid_size']
    steps = config['steps']
    
    # Initialize state
    state = np.random.randint(0, 2, (grid_size, grid_size))
    
    metrics_history = []
    monitor = HealthMonitor()
    
    for step in range(steps):
        start_time = time.time()
        
        # Run step
        new_state = eco_director_step(state, config)
        
        # Calculate metrics
        coherence = float(np.mean(state)) # Placeholder
        diversity = float(np.std(state))  # Placeholder
        step_latency = time.time() - start_time
        
        current_memory = 0 # Placeholder, actual monitoring done in CLI
        
        # Validate metrics
        current_metrics = {
            "coherence_score": coherence,
            "diversity_score": diversity,
            "step_latency": step_latency
        }
        
        validation = monitor.validate_metrics_and_handle(current_metrics, step=step)
        
        if not validation['valid']:
            # Graceful handling: log warning but continue or break depending on policy
            # For now, we continue but flag the run
            pass
        
        metrics_history.append({
            "step": step,
            "metrics": current_metrics,
            "valid": validation['valid']
        })
        
        state = new_state

    return {
        "config": config,
        "final_state_shape": state.shape,
        "metrics_history": metrics_history,
        "warnings": monitor.warnings,
        "has_nan": monitor.has_nan,
        "has_explosion": monitor.has_explosion
    }

def inject_runtime_params(config: Dict[str, Any], runtime_params: Dict[str, Any]) -> Dict[str, Any]:
    """Merges runtime parameters into config."""
    updated = config.copy()
    updated.update(runtime_params)
    return updated

def update_config_from_args(config: Dict[str, Any], args: Any) -> Dict[str, Any]:
    """Updates config from argparse namespace."""
    runtime = {}
    if hasattr(args, 'steps') and args.steps:
        runtime['steps'] = args.steps
    if hasattr(args, 'grid_size') and args.grid_size:
        runtime['grid_size'] = args.grid_size
    return inject_runtime_params(config, runtime)

def load_and_inject_config(config_path: str, args: Optional[Any] = None) -> Dict[str, Any]:
    """Loads config and injects runtime params if args provided."""
    config = load_config(config_path)
    if args:
        config = update_config_from_args(config, args)
    return config
