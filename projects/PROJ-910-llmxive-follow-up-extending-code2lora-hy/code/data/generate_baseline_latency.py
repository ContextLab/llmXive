import sys
import logging
from pathlib import Path
from utils.latency_monitor import measure_baseline_generation_latency, ensure_results_dir
from evaluation.baseline_loader import get_baseline_adapter_path
import json

def main():
    """
    Main entry point for generating baseline latency measurement.
    
    This script measures the time taken to load the baseline neural-encoder adapter
    and saves the result to data/results/baseline_generation_latency.json.
    """
    try:
        # Ensure results directory exists
        results_dir = ensure_results_dir()
        
        # Get baseline adapter path for reference
        baseline_path = get_baseline_adapter_path()
        logging.info(f"Baseline adapter path: {baseline_path}")
        
        # Measure the latency
        logging.info("Measuring baseline generation latency...")
        start_time = time.perf_counter()
        
        # Import and run the baseline adapter loading
        from evaluation.baseline_loader import load_baseline_adapter
        adapter_model = load_baseline_adapter()
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        
        # Prepare the result
        result = {
            "baseline_generation_latency_seconds": elapsed_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "baseline_adapter_path": str(baseline_path),
            "measurement_method": "time.perf_counter"
        }
        
        # Save to JSON file
        output_path = results_dir / "baseline_generation_latency.json"
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logging.info(f"Baseline generation latency: {elapsed_time:.4f} seconds")
        logging.info(f"Results saved to {output_path}")
        
        return result
        
    except Exception as e:
        logging.error(f"Failed to measure baseline generation latency: {e}")
        raise

if __name__ == "__main__":
    import time
    import logging
    from utils.logging import setup_logging
    
    setup_logging()
    main()
