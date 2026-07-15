"""
Output writer for simulation results.
Implements T016: Write output results to data/simulation/p_values_raw.csv.
"""
import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from code.simulation.logging_config import get_logger, log_operation

logger = get_logger("output_writer")

def ensure_output_directory():
    """Ensure the output directory exists."""
    os.makedirs("data/simulation", exist_ok=True)

def write_p_values_raw(p_values: List[Dict[str, Any]], filepath: str = "data/simulation/p_values_raw.csv", overwrite: bool = True):
    """
    Write p-values to CSV.
    """
    ensure_output_directory()
    
    if overwrite or not os.path.exists(filepath):
        mode = 'w'
    else:
        mode = 'a'
    
    with open(filepath, mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["test_type", "sample_size", "effect_size", "hypothesis", "p_value", "timestamp"])
        if overwrite or not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            writer.writeheader()
        
        for p in p_values:
            writer.writerow({
                "test_type": p.get("test_type", "unknown"),
                "sample_size": p.get("sample_size", 0),
                "effect_size": p.get("effect_size", 0.0),
                "hypothesis": p.get("hypothesis", "unknown"),
                "p_value": p.get("p_value", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    logger.log("p_values_written", path=filepath, count=len(p_values))

def load_p_values_raw(filepath: str = "data/simulation/p_values_raw.csv") -> List[Dict[str, Any]]:
    """
    Load p-values from CSV.
    """
    if not os.path.exists(filepath):
        return []
    
    try:
        df = pd.read_csv(filepath)
        return df.to_dict('records')
    except Exception as e:
        logger.log("failed_to_load_p_values", error=str(e))
        return []

def load_p_values_raw_safe(filepath: str = "data/simulation/p_values_raw.csv") -> Optional[pd.DataFrame]:
    """
    Load p-values from CSV safely.
    """
    if not os.path.exists(filepath):
        return None
    try:
        return pd.read_csv(filepath)
    except Exception:
        return None

def main():
    """Main entry point for testing."""
    logger.log("output_writer_main")

if __name__ == "__main__":
    main()
