import logging
import csv
import os
from typing import Dict, Any, List

def setup_logging(level: int = logging.INFO) -> None:
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('simulation.log')
        ]
    )

def write_csv_row(filepath: str, row: Dict[str, Any]) -> None:
    """Append a row to the CSV file."""
    file_exists = os.path.exists(filepath)
    fieldnames = ['seed', 'N', 'p', 'avg_degree', 'conductivity', 'percolation_flag', 'scaling_factor']
    
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        
        # Ensure all required fields are present
        write_row = {k: row.get(k, '') for k in fieldnames}
        writer.writerow(write_row)

def format_error(e: Exception) -> str:
    """Format exception for logging."""
    return f"{type(e).__name__}: {str(e)}"
