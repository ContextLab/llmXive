import json
import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_batch_results(output_dir: str) -> List[Dict[str, Any]]:
    """
    Load all JSON result files from the batch output directory.
    Expects files named like 'scene_<id>_results.json' or similar in output_dir.
    """
    results = []
    output_path = Path(output_dir)
    
    if not output_path.exists():
        logger.warning(f"Output directory {output_dir} does not exist. Returning empty results.")
        return results

    json_files = list(output_path.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files in {output_dir}")

    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Filter out non-result files (e.g., checksums_temp.json, threshold_result.json)
                if 'view_count' in data and ('latency' in data or 'status' in data):
                    results.append(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            continue

    return results

def aggregate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate results into a flat list suitable for CSV export.
    Ensures all required columns are present, filling with None if missing.
    """
    aggregated = []
    
    for result in results:
        # Skip entries that are explicitly skipped (e.g., baseline CPU unsupported)
        if result.get('status') == 'skipped':
            # We might still want to log this, but for CSV we typically focus on successful runs
            # or include a row with NaN/nulls. Let's include it with nulls for clarity.
            row = {
                'view_count': result.get('view_count'),
                'latency': None,
                'chamfer_distance': None,
                'psnr': None,
                'baseline_latency': None
            }
            aggregated.append(row)
            continue

        row = {
            'view_count': result.get('view_count'),
            'latency': result.get('latency'),
            'chamfer_distance': result.get('chamfer_distance'),
            'psnr': result.get('psnr'),
            'baseline_latency': result.get('baseline_latency')
        }
        aggregated.append(row)

    return aggregated

def write_csv(aggregated_results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write the aggregated results to a CSV file.
    Columns: view_count, latency, chamfer_distance, psnr, baseline_latency
    """
    if not aggregated_results:
        logger.warning("No results to write to CSV.")
        # Ensure the directory exists even if empty
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['view_count', 'latency', 'chamfer_distance', 'psnr', 'baseline_latency'])
            writer.writeheader()
        return

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['view_count', 'latency', 'chamfer_distance', 'psnr', 'baseline_latency']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in aggregated_results:
            writer.writerow(row)

    logger.info(f"Benchmark CSV written to {output_path}")

def main():
    """
    Main entry point for generating the benchmark trade-off CSV.
    Reads from the default batch output directory (data/processed/) and writes to data/processed/benchmark_tradeoff.csv.
    """
    # Default paths
    output_dir = "data/processed"
    csv_output_path = "data/processed/benchmark_tradeoff.csv"
    
    # Allow override via environment or args if needed, but sticking to task spec paths
    logger.info(f"Loading batch results from {output_dir}")
    results = load_batch_results(output_dir)
    
    if not results:
        logger.warning("No valid benchmark results found. Generating empty CSV.")
    
    logger.info(f"Aggregating {len(results)} results")
    aggregated = aggregate_results(results)
    
    logger.info(f"Writing CSV to {csv_output_path}")
    write_csv(aggregated, csv_output_path)

if __name__ == "__main__":
    main()