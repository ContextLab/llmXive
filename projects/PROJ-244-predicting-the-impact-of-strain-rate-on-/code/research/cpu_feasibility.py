import os
import sys
import json
import logging
import resource
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "cpu_feasibility.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_available_ram_gb() -> float:
    """
    Get available RAM in GB.
    """
    try:
        # Linux
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    # Value is in kB
                    mem_kb = int(line.split()[1])
                    return mem_kb / (1024 * 1024)
    except FileNotFoundError:
        # Fallback for macOS/Windows (approximate)
        try:
            import psutil
            return psutil.virtual_memory().available / (1024 * 1024)
        except ImportError:
            logger.warning("psutil not installed. Using a default estimate of 8GB.")
            return 8.0
    return 8.0 # Default fallback

def load_sample_estimates() -> Dict[str, Any]:
    """
    Load sample size estimates to calculate memory footprint.
    """
    estimates_path = DATA_DIR / "sample_size_estimate.json"
    if estimates_path.exists():
        with open(estimates_path, 'r') as f:
            return json.load(f)
    return {"total_sample_size": 1000, "per_family_counts": {}}

def estimate_memory_footprint(sample_size: int, rows_per_mb: int = 10000) -> float:
    """
    Estimate memory footprint in GB.
    Assumes a rough average of 10,000 rows per MB for a typical dataframe with ~20 columns.
    Adjust rows_per_mb based on actual column count and data types if needed.
    """
    # Rough estimation: 10,000 rows * ~20 columns * 8 bytes (float64) + overhead
    # This is a simplified heuristic.
    estimated_mb = sample_size / rows_per_mb
    return estimated_mb / 1024

def check_feasibility(sample_size_data: Dict[str, Any], max_ram_gb: Optional[float] = None) -> Dict[str, Any]:
    """
    Check if the estimated data subset fits in available RAM.
    """
    if max_ram_gb is None:
        max_ram_gb = get_available_ram_gb()
    
    total_n = sample_size_data.get("total_sample_size", 0)
    estimated_gb = estimate_memory_footprint(total_n)
    
    is_feasible = estimated_gb < max_ram_gb
    
    return {
        "total_sample_size": total_n,
        "estimated_memory_gb": estimated_gb,
        "available_memory_gb": max_ram_gb,
        "is_feasible": is_feasible,
        "status": "Feasible" if is_feasible else "Infeasible"
    }

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the CPU feasibility report to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"CPU feasibility report saved to {output_path}")

def main():
    """
    Main entry point for CPU feasibility check (T011).
    """
    logger.info("Starting CPU feasibility check (T011).")
    
    sample_data = load_sample_estimates()
    report = check_feasibility(sample_data)
    
    output_path = DATA_DIR / "cpu_feasibility_report.json"
    save_report(report, output_path)
    
    logger.info(f"Estimated Memory: {report['estimated_memory_gb']:.4f} GB")
    logger.info(f"Available Memory: {report['available_memory_gb']:.4f} GB")
    logger.info(f"Feasibility Status: {report['status']}")
    
    return 0 if report['is_feasible'] else 1

if __name__ == "__main__":
    sys.exit(main())