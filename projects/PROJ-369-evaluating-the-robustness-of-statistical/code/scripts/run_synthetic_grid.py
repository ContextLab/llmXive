"""
Script to generate synthetic series for the N-variation grid.

Generates fractional Gaussian noise (fGn) series with lengths:
{100, 500, 1000, 5000, 10000}

Uses the existing generators.py API to create the series and saves them
to the processed data directory.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.synthesis.generators import generate_synthetic_series
from src.utils.config import get_path, set_seed
from src.utils.logging import setup_logger, log_info, log_error, log_warning

# Configuration
HURST_VALUES = [0.5, 0.7, 0.8, 0.9]
LENGTHS = [100, 500, 1000, 5000, 10000]
RANDOM_SEED = 42

def generate_grid():
    """Generate synthetic series for all combinations of H and N."""
    set_seed(RANDOM_SEED)
    logger = setup_logger("synthetic_grid")
    
    output_dir = get_path("data_processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for h in HURST_VALUES:
        for n in LENGTHS:
            try:
                log_info(logger, f"Generating series: H={h}, N={n}")
                
                # Generate the series using the existing generator
                series_data = generate_synthetic_series(
                    hurst_exponent=h,
                    length=n,
                    seed=RANDOM_SEED + int(h * 1000) + n
                )
                
                # Create a unique identifier for this series
                series_id = f"synthetic_H{h}_N{n}"
                
                # Save the series to a CSV file
                output_path = output_dir / f"{series_id}.csv"
                series_data.to_csv(output_path, index=True)
                
                log_info(logger, f"Saved series to {output_path}")
                
                # Record the result
                results.append({
                    "series_id": series_id,
                    "hurst_exponent": h,
                    "length": n,
                    "output_path": str(output_path),
                    "status": "success"
                })
                
            except Exception as e:
                log_error(logger, f"Failed to generate series H={h}, N={n}: {str(e)}")
                results.append({
                    "series_id": f"synthetic_H{h}_N{n}",
                    "hurst_exponent": h,
                    "length": n,
                    "output_path": None,
                    "status": "failed",
                    "error": str(e)
                })
    
    # Save the results summary
    summary_path = output_dir / "synthetic_grid_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    log_info(logger, f"Generated {len([r for r in results if r['status'] == 'success'])} series successfully")
    log_info(logger, f"Summary saved to {summary_path}")
    
    return results

def main():
    """Main entry point."""
    logger = setup_logger("synthetic_grid")
    log_info(logger, "Starting synthetic grid generation")
    
    try:
        results = generate_grid()
        success_count = len([r for r in results if r['status'] == 'success'])
        total_count = len(results)
        
        log_info(logger, f"Completed: {success_count}/{total_count} series generated successfully")
        
        if success_count == total_count:
            log_info(logger, "All series generated successfully")
            return 0
        else:
            log_warning(logger, f"Some series failed: {total_count - success_count} failures")
            return 1
            
    except Exception as e:
        log_error(logger, f"Fatal error in synthetic grid generation: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
