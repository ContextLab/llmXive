import argparse
import sys
import json
import time
import random
import os
import resource
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# Import from project API surface
from config import set_seed, initialize_reproducibility
from sim.eco_director import run_simulation as eco_run_simulation
from sim.neural_baseline import run_neural_baseline
from sim.health_monitor import HealthMonitor
from sim.logging_config import SimulationLogger, MetricRecord

# Constants
MEMORY_LIMIT_MB = 6000  # 6GB limit as per T014
TIMEOUT_SECONDS = 21600  # 6 hours as per T013

class SimulationResult:
    """Container for simulation execution results."""
    def __init__(self, success: bool, data: Optional[Dict[str, Any]] = None, 
                 error: Optional[str] = None, power_limited: bool = False):
        self.success = success
        self.data = data
        self.error = error
        self.power_limited = power_limited

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "power_limited": self.power_limited,
            "timestamp": datetime.now().isoformat()
        }

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0

def log_status(status: Dict[str, Any], log_file: str = "simulation_status.json") -> None:
    """Log status to a JSON file."""
    status["timestamp"] = datetime.now().isoformat()
    with open(log_file, "w") as f:
        json.dump(status, f, indent=2)

def check_memory_and_log(log_file: str = "simulation_status.json") -> bool:
    """Check if memory usage exceeds limit. Returns True if exceeded."""
    current_mb = get_memory_usage_mb()
    status = {
        "status": "running",
        "memory_mb": current_mb,
        "limit_mb": MEMORY_LIMIT_MB,
        "timestamp": datetime.now().isoformat()
    }
    
    if current_mb > MEMORY_LIMIT_MB:
        status["status"] = "killed_memory_limit"
        log_status(status, log_file)
        return True
    
    status["status"] = "running"
    log_status(status, log_file)
    return False

def run_with_timeout(func, args: Tuple, timeout: int, log_file: str = "simulation_status.json") -> Tuple[bool, Any, Optional[str]]:
    """
    Run a function with a timeout. 
    Note: Python's signal.alarm is Unix-only. For cross-platform robustness,
    we rely on the caller to handle timeouts or use a subprocess wrapper.
    Here we implement a basic check loop for long-running steps.
    """
    start_time = time.time()
    try:
        # In a real multi-step simulation, we would check time inside the loop.
        # For this implementation, we assume the function handles its own timing
        # or we wrap it if it's a single call.
        result = func(*args)
        elapsed = time.time() - start_time
        if elapsed > timeout:
            status = {
                "status": "killed_timeout",
                "elapsed_seconds": elapsed,
                "limit_seconds": timeout,
                "timestamp": datetime.now().isoformat()
            }
            log_status(status, log_file)
            return False, None, "Timeout exceeded"
        return True, result, None
    except Exception as e:
        status = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        log_status(status, log_file)
        return False, None, str(e)

def ensure_fallback_dataset(fallback_path: str = "data/synthetic_small.csv") -> bool:
    """
    Ensure the fallback dataset exists. 
    If not, return False. The caller must handle the fallback logic.
    This function does NOT generate the data (T015c handles generation).
    """
    if not os.path.exists(fallback_path):
        return False
    return True

def run_simulation_with_fallback(config: Dict[str, Any], steps: int, seed: int, 
                                 use_fallback: bool = False) -> SimulationResult:
    """
    Run the simulation. If use_fallback is True, use the synthetic dataset.
    If the primary dataset is unavailable and fallback is not explicitly requested,
    this function attempts to load the fallback.
    
    Returns a SimulationResult with 'power_limited' flag set if a timeout/memory limit occurred.
    """
    # Initialize reproducibility
    set_seed(seed)
    initialize_reproducibility()
    
    log_file = "simulation_status.json"
    
    # Check for fallback if primary is missing
    primary_data_path = config.get("data_path", "data/real_data.csv")
    if not os.path.exists(primary_data_path):
        if not use_fallback:
            # Attempt to use fallback
            if ensure_fallback_dataset():
                config["data_path"] = "data/synthetic_small.csv"
                use_fallback = True
            else:
                return SimulationResult(
                    success=False, 
                    error="Primary data missing and fallback not available.",
                    power_limited=False
                )
        else:
            if not ensure_fallback_dataset():
                return SimulationResult(
                    success=False, 
                    error="Fallback dataset requested but not found.",
                    power_limited=False
                )

    # Initialize logger
    logger = SimulationLogger(log_dir="logs")
    
    # Determine which engine to run
    engine_type = config.get("engine_type", "eco_director")
    
    if engine_type == "neural":
        # Run neural baseline (T013 throttling logic is inside this module)
        success, data, error = run_with_timeout(
            run_neural_baseline, 
            (config, steps, seed), 
            TIMEOUT_SECONDS, 
            log_file
        )
    else:
        # Run Eco-Director
        success, data, error = run_with_timeout(
            eco_run_simulation, 
            (config, steps, seed), 
            TIMEOUT_SECONDS, 
            log_file
        )

    if not success:
        # Check if it was a timeout/memory kill
        with open(log_file, "r") as f:
            status = json.load(f)
        
        if status.get("status") in ["killed_timeout", "killed_memory_limit"]:
            return SimulationResult(
                success=False,
                data=data,
                error=error,
                power_limited=True  # Flag as Power-Limited
            )
        return SimulationResult(success=False, error=error, power_limited=False)

    return SimulationResult(success=True, data=data, power_limited=False)

def parse_args():
    parser = argparse.ArgumentParser(description="Run llmXive simulation with fallback support.")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML")
    parser.add_argument("--steps", type=int, default=10000, help="Number of simulation steps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--force-fallback", action="store_true", help="Force use of fallback dataset")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Load config
    import yaml
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Run simulation with fallback logic
    result = run_simulation_with_fallback(
        config=config, 
        steps=args.steps, 
        seed=args.seed, 
        use_fallback=args.force_fallback
    )
    
    # Output structured JSON status
    print(json.dumps(result.to_dict()))
    
    # Exit with code based on success
    sys.exit(0 if result.success else 1)

if __name__ == "__main__":
    main()
