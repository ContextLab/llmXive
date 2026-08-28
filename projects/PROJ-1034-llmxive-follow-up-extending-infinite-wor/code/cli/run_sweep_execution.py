import os
import sys
import json
import time
import argparse
import csv
from typing import List, Dict, Any, Optional

# Add project root to path for imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config import set_seed, initialize_reproducibility
from sim.eco_director import load_config, validate_config, run_simulation
from sim.neural_baseline import run_neural_baseline_proxy
from sim.logging_config import create_logger, SimulationLogger, MetricRecord
from sim.health_monitor import HealthMonitor
from data.generate_synthetic import generate_synthetic_data, write_csv

def log_status(status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log a structured status message to stdout."""
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status,
        "details": details or {}
    }
    print(json.dumps(payload))

def ensure_fallback_dataset(output_path: str, size: int = 1000) -> None:
    """
    Generate a synthetic fallback dataset if real data is unavailable.
    This is a last-resort mechanism for testing the pipeline flow.
    """
    if os.path.exists(output_path):
        return
    
    log_status("fallback_dataset_generation", {"path": output_path, "size": size})
    data = generate_synthetic_data(size)
    write_csv(data, output_path)
    log_status("fallback_dataset_ready", {"path": output_path})

def run_configuration(
    config_id: str,
    params: Dict[str, Any],
    steps: int,
    seed: int,
    output_dir: str,
    use_fallback: bool = False
) -> Dict[str, Any]:
    """
    Execute a single simulation configuration.
    
    Args:
        config_id: Unique identifier for this configuration
        params: Dictionary of simulation parameters
        steps: Number of time-steps to run
        seed: Random seed for reproducibility
        output_dir: Directory to write raw logs
        use_fallback: If True, force synthetic data generation
      
    Returns:
        Dictionary containing execution results and metadata
    """
    # Initialize reproducibility
    initialize_reproducibility(seed)
    set_seed(seed)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup logging for this run
    log_path = os.path.join(output_dir, f"run_{config_id}_raw.jsonl")
    logger = create_logger(log_path)
    
    # Setup health monitor
    monitor = HealthMonitor(max_memory_mb=6000, max_time_sec=3600)
    
    # Start monitoring
    monitor.start()
    
    result = {
        "config_id": config_id,
        "seed": seed,
        "steps_requested": steps,
        "steps_completed": 0,
        "status": "success",
        "metrics": {},
        "errors": []
    }
    
    try:
        log_status("simulation_start", {"config_id": config_id, "steps": steps})
        
        # Run CA Simulation
        ca_start = time.time()
        ca_result = run_simulation(
            params=params,
            steps=steps,
            seed=seed,
            logger=logger,
            monitor=monitor
        )
        ca_duration = time.time() - ca_start
        
        result["ca_duration"] = ca_duration
        result["ca_final_state_shape"] = ca_result.get("final_state", {}).shape if hasattr(ca_result.get("final_state"), "shape") else None
        result["ca_steps_completed"] = ca_result.get("steps_completed", 0)
        
        # Run Neural Baseline
        baseline_start = time.time()
        baseline_result = run_neural_baseline_proxy(
            params=params,
            steps=steps,
            seed=seed,
            logger=logger,
            monitor=monitor
        )
        baseline_duration = time.time() - baseline_start
        
        result["baseline_duration"] = baseline_duration
        result["baseline_steps_completed"] = baseline_result.get("steps_completed", 0)
        
        # Aggregate metrics
        result["metrics"] = {
            "coherence_score": ca_result.get("metrics", {}).get("coherence_score", 0.0),
            "diversity_score": ca_result.get("metrics", {}).get("diversity_score", 0.0),
            "ca_step_latency_avg": ca_result.get("metrics", {}).get("step_latency_avg", 0.0),
            "baseline_step_latency_avg": baseline_result.get("metrics", {}).get("step_latency_avg", 0.0),
            "total_steps": ca_result.get("steps_completed", 0)
        }
        
        log_status("simulation_complete", {
            "config_id": config_id,
            "ca_duration": ca_duration,
            "baseline_duration": baseline_duration
        })
        
    except MemoryError as e:
        result["status"] = "memory_limit_exceeded"
        result["errors"].append(str(e))
        log_status("simulation_failed", {"config_id": config_id, "error": "memory_limit_exceeded"})
        
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        log_status("simulation_failed", {"config_id": config_id, "error": str(e)})
        
    finally:
        monitor.stop()
        # Final log flush
        logger.close()
        
    return result

def main():
    parser = argparse.ArgumentParser(description="Execute simulation sweep configurations")
    parser.add_argument("--config-file", type=str, required=True, help="Path to CSV with configurations")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory for raw output logs")
    parser.add_argument("--steps", type=int, default=10000, help="Number of time-steps per configuration")
    parser.add_argument("--seed-base", type=int, default=42, help="Base seed for configuration seeds")
    parser.add_argument("--fallback", action="store_true", help="Force fallback dataset generation")
    
    args = parser.parse_args()
    
    log_status("sweep_execution_start", {
        "config_file": args.config_file,
        "output_dir": args.output_dir,
        "steps": args.steps
    })
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load configurations
    if not os.path.exists(args.config_file):
        log_status("error", {"message": f"Config file not found: {args.config_file}"})
        sys.exit(1)
    
    configs = []
    with open(args.config_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse params from JSON string if needed
            try:
                params = json.loads(row.get('params', '{}'))
            except json.JSONDecodeError:
                params = row # Fallback if not JSON string
            
            configs.append({
                "id": row.get('id', f"config_{len(configs)}"),
                "params": params,
                "seed": args.seed_base + len(configs)
            })
    
    log_status("configurations_loaded", {"count": len(configs)})
    
    # Execute each configuration
    all_results = []
    for i, config in enumerate(configs):
        log_status("processing_configuration", {
            "index": i,
            "total": len(configs),
            "config_id": config["id"]
        })
        
        result = run_configuration(
            config_id=config["id"],
            params=config["params"],
            steps=args.steps,
            seed=config["seed"],
            output_dir=args.output_dir,
            use_fallback=args.fallback
        )
        
        all_results.append(result)
        
        # Write individual result log
        result_path = os.path.join(args.output_dir, f"result_{config['id']}.json")
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
    
    # Write summary
    summary_path = os.path.join(args.output_dir, "sweep_summary.json")
    with open(summary_path, 'w') as f:
        json.dump({
            "total_configurations": len(configs),
            "successful": sum(1 for r in all_results if r["status"] == "success"),
            "failed": sum(1 for r in all_results if r["status"] != "success"),
            "results": all_results
        }, f, indent=2)
    
    log_status("sweep_execution_complete", {
        "total": len(configs),
        "successful": sum(1 for r in all_results if r["status"] == "success"),
        "failed": sum(1 for r in all_results if r["status"] != "success")
    })

if __name__ == "__main__":
    main()