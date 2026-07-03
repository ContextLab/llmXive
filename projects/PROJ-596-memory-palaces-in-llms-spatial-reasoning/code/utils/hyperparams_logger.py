import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Constants matching the project's memory constraints
RAM_THRESHOLD_GB = 6.0

def get_current_memory_usage_gb() -> float:
    """
    Returns the current RSS (Resident Set Size) memory usage in GB.
    Uses psutil if available, otherwise falls back to a simple estimation
    or returns 0.0 if not measurable.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    except ImportError:
        # Fallback: Try reading /proc/self/status on Linux
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        rss_kb = int(line.split()[1])
                        return rss_kb / (1024 ** 2)
        except Exception:
            pass
    return 0.0

def log_hyperparameters(
    run_id: str,
    base_batch_size: int,
    effective_batch_size: int,
    dataset_size: int,
    effective_dataset_size: int,
    model_name: str,
    memory_threshold_gb: float = RAM_THRESHOLD_GB,
    memory_usage_at_start_gb: Optional[float] = None,
    memory_usage_at_end_gb: Optional[float] = None,
    deviations: Optional[List[Dict[str, Any]]] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Logs the final effective hyperparameters and any deviations (e.g., batch-size
    reduction, dataset capping) to artifacts/results/hyperparams_log.json.
    
    Explicitly notes the RAM threshold (FR-003) and documents the decision logic.
    
    Args:
        run_id: Unique identifier for the run.
        base_batch_size: The originally requested batch size.
        effective_batch_size: The actual batch size used after memory adjustments.
        dataset_size: Original size of the dataset.
        effective_dataset_size: Actual size of the dataset used (if capped).
        model_name: Name of the model used.
        memory_threshold_gb: The RAM threshold in GB that triggers adjustments.
        memory_usage_at_start_gb: RSS at start of run.
        memory_usage_at_end_gb: RSS at end of run.
        deviations: List of deviation records (e.g., {"type": "batch_size_reduction", "reason": "RSS > 6GB"}).
        output_dir: Directory to write the log. Defaults to artifacts/results/.
    
    Returns:
        Path to the written JSON file.
    """
    if output_dir is None:
        output_dir = Path("artifacts/results")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "hyperparams_log.json"
    
    # Load existing log if it exists to append to it
    existing_log = []
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                existing_log = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_log = []
    
    # Ensure deviations is a list
    if deviations is None:
        deviations = []
    
    # Determine if deviations occurred based on inputs if not explicitly provided
    if not deviations:
        if effective_batch_size < base_batch_size:
            deviations.append({
                "type": "batch_size_reduction",
                "original": base_batch_size,
                "effective": effective_batch_size,
                "reason": f"Memory usage exceeded {memory_threshold_gb}GB threshold (FR-003)"
            })
        if effective_dataset_size < dataset_size:
            deviations.append({
                "type": "dataset_capping",
                "original": dataset_size,
                "effective": effective_dataset_size,
                "reason": f"Memory usage exceeded {memory_threshold_gb}GB threshold after batch size reduction (FR-003)"
            })
    
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "run_id": run_id,
        "ram_threshold_gb": memory_threshold_gb,
        "hyperparameters": {
            "base_batch_size": base_batch_size,
            "effective_batch_size": effective_batch_size,
            "base_dataset_size": dataset_size,
            "effective_dataset_size": effective_dataset_size,
            "model_name": model_name
        },
        "memory_snapshot": {
            "start_gb": memory_usage_at_start_gb,
            "end_gb": memory_usage_at_end_gb
        },
        "deviations": deviations,
        "notes": "Log generated per FR-003: Explicitly notes 6GB RAM threshold and deviations."
    }
    
    existing_log.append(entry)
    
    with open(output_path, 'w') as f:
        json.dump(existing_log, f, indent=2)
    
    return output_path

def main():
    """
    CLI entry point for testing the hyperparameters logger.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Log hyperparameters and deviations.")
    parser.add_argument("--run_id", type=str, default="test_run_001", help="Run ID")
    parser.add_argument("--base_batch_size", type=int, default=8, help="Original batch size")
    parser.add_argument("--effective_batch_size", type=int, default=4, help="Effective batch size")
    parser.add_argument("--dataset_size", type=int, default=10000, help="Original dataset size")
    parser.add_argument("--effective_dataset_size", type=int, default=10000, help="Effective dataset size")
    parser.add_argument("--model_name", type=str, default="gpt2-medium", help="Model name")
    parser.add_argument("--threshold", type=float, default=RAM_THRESHOLD_GB, help="RAM threshold")
    
    args = parser.parse_args()
    
    start_mem = get_current_memory_usage_gb()
    
    # Simulate some work or just log immediately
    time.sleep(0.1)
    
    end_mem = get_current_memory_usage_gb()
    
    deviations = []
    if args.effective_batch_size < args.base_batch_size:
        deviations.append({
            "type": "batch_size_reduction",
            "original": args.base_batch_size,
            "effective": args.effective_batch_size,
            "reason": f"Memory usage exceeded {args.threshold}GB threshold (FR-003)"
        })
    
    if args.effective_dataset_size < args.dataset_size:
        deviations.append({
            "type": "dataset_capping",
            "original": args.dataset_size,
            "effective": args.effective_dataset_size,
            "reason": f"Memory usage exceeded {args.threshold}GB threshold after batch size reduction (FR-003)"
        })
    
    output_path = log_hyperparameters(
        run_id=args.run_id,
        base_batch_size=args.base_batch_size,
        effective_batch_size=args.effective_batch_size,
        dataset_size=args.dataset_size,
        effective_dataset_size=args.effective_dataset_size,
        model_name=args.model_name,
        memory_threshold_gb=args.threshold,
        memory_usage_at_start_gb=start_mem,
        memory_usage_at_end_gb=end_mem,
        deviations=deviations
    )
    
    print(f"Hyperparameters logged to: {output_path}")
    
    # Read and print the content to verify
    with open(output_path, 'r') as f:
        print(f.read())

if __name__ == "__main__":
    main()