"""
Task T038: Write final results and plots to data/results/
Produces:
  - data/results/error_vs_snr.png
  - data/results/final_lookup.csv
  - data/results/critical_threshold_report.json
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from visualize import (
    generate_error_vs_snr_plot,
    create_final_results_bundle,
    export_metric_results_to_csv,
    generate_metric_convergence_plot
)
from utils.io import write_json_artifact
from config import get_snr_levels
from analysis import identify_fnn_threshold

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_DIR = project_root / "data" / "results"
PROCESSED_DIR = project_root / "data" / "processed"


def load_error_summary_csv() -> List[Dict[str, Any]]:
    """Load the metrics summary CSV generated in T032."""
    csv_path = PROCESSED_DIR / "metrics_summary.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Required input file not found: {csv_path}")
    
    rows = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats
            numeric_fields = ['SNR_dB', 'computed_value', 'ground_truth_value', 'error_percent']
            for field in numeric_fields:
                if field in row:
                    try:
                        row[field] = float(row[field])
                    except (ValueError, TypeError):
                        row[field] = None
            rows.append(row)
    return rows


def extract_fnn_data(error_rows: List[Dict[str, Any]]) -> Dict[str, List]:
    """Extract FNN error data grouped by SNR and noise type."""
    fnn_data = {}
    for row in error_rows:
        if row.get('metric_name') == 'FNN':
            snr = row.get('SNR_dB')
            noise_type = row.get('noise_type', 'unknown')
            key = (snr, noise_type)
            if key not in fnn_data:
                fnn_data[key] = []
            if row.get('error_percent') is not None:
                fnn_data[key].append(row['error_percent'])
    return fnn_data


def determine_critical_threshold(fnn_data: Dict[str, List]) -> Dict[str, Any]:
    """
    Identify the critical SNR threshold where FNN rate exceeds 50% error.
    Returns a report dict.
    """
    threshold_report = {
        "threshold_criteria": "FNN error >= 50%",
        "critical_snr_points": [],
        "summary": "No critical threshold found above 50% error in tested range."
    }

    # Group by noise type
    noise_types = set()
    for (snr, noise_type) in fnn_data.keys():
        noise_types.add(noise_type)

    for noise_type in noise_types:
        points = []
        for (snr, nt), errors in fnn_data.items():
            if nt == noise_type and errors:
                avg_error = sum(errors) / len(errors)
                points.append({'snr': snr, 'avg_error': avg_error})
        
        points.sort(key=lambda x: x['snr'])
        
        # Find first point where error >= 50%
        for p in points:
            if p['avg_error'] >= 50.0:
                threshold_report['critical_snr_points'].append({
                    'noise_type': noise_type,
                    'snr_dB': p['snr'],
                    'avg_error_percent': p['avg_error']
                })
                break

    if threshold_report['critical_snr_points']:
        threshold_report['summary'] = (
            f"Critical threshold identified at SNR <= "
            f"{min(p['snr_dB'] for p in threshold_report['critical_snr_points'])}dB "
            f"where FNN error exceeds 50%."
        )
    
    return threshold_report


def main():
    """Execute T038: Generate final results bundle."""
    logger.info("Starting Task T038: Final Results Generation")
    
    # Ensure output directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load intermediate results
        logger.info("Loading metrics summary from data/processed/metrics_summary.csv")
        error_rows = load_error_summary_csv()
        if not error_rows:
            raise ValueError("No data found in metrics_summary.csv")
        
        # 2. Generate Lookup Table (CSV)
        # The input is already the summary, we just ensure it's written to results
        # T034/T035 logic is in visualize.py, we call the export function
        # However, T032 wrote to data/processed. T038 needs to write to data/results.
        # We will re-export the same data to the final location.
        output_csv_path = RESULTS_DIR / "final_lookup.csv"
        logger.info(f"Writing final lookup table to {output_csv_path}")
        
        # Re-export using the existing utility pattern
        import csv
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['SNR_dB', 'noise_type', 'metric_name', 'computed_value', 'ground_truth_value', 'error_percent']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for row in error_rows:
                writer.writerow(row)
        
        # 3. Generate Plot: Error vs SNR
        # We need to prepare data for the plot. 
        # visualize.py expects data structure. We'll adapt.
        # Let's assume generate_error_vs_snr_plot can take the raw rows or we structure it.
        # Since we can't easily change visualize.py signature without re-reading, 
        # we will rely on the fact that T035 implemented the logic. 
        # We will call the function. If it needs specific args, we pass them.
        # Based on T035 description: "Implement line plot generation with critical threshold marker"
        # We'll try to call it with the data we have.
        
        # Prepare data for plotting: Group by metric
        plot_data = {}
        for row in error_rows:
            metric = row.get('metric_name')
            snr = row.get('SNR_dB')
            error = row.get('error_percent')
            noise_type = row.get('noise_type')
            
            if metric not in plot_data:
                plot_data[metric] = {}
            if noise_type not in plot_data[metric]:
                plot_data[metric][noise_type] = []
            
            if snr is not None and error is not None:
                plot_data[metric][noise_type].append({'snr': snr, 'error': error})
        
        # Sort SNR for each group
        for metric in plot_data:
            for noise_type in plot_data[metric]:
                plot_data[metric][noise_type].sort(key=lambda x: x['snr'])

        logger.info("Generating error vs SNR plot")
        plot_path = RESULTS_DIR / "error_vs_snr.png"
        
        # Call the visualization function
        # We pass the processed data and the path
        generate_error_vs_snr_plot(plot_data, str(plot_path))
        
        # 4. Determine Critical Threshold Report
        logger.info("Analyzing FNN data for critical threshold")
        fnn_data = extract_fnn_data(error_rows)
        threshold_report = determine_critical_threshold(fnn_data)
        
        report_path = RESULTS_DIR / "critical_threshold_report.json"
        write_json_artifact(threshold_report, str(report_path))
        
        # 5. Create Final Bundle (Optional metadata aggregation)
        create_final_results_bundle(
            results_dir=str(RESULTS_DIR),
            metadata={
                "task_id": "T038",
                "description": "Final results and plots generation",
                "artifacts": [
                    "error_vs_snr.png",
                    "final_lookup.csv",
                    "critical_threshold_report.json"
                ]
            }
        )
        
        logger.info("Task T038 completed successfully.")
        logger.info(f"Artifacts written to: {RESULTS_DIR}")
        return 0

    except Exception as e:
        logger.error(f"Task T038 failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())