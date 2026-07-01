"""
Export script to generate participant-level CSV with structural and avalanche metrics.

This script aggregates results from:
- Structural metrics (degree, clustering, rich-club) from code/analysis/metrics.py
- Avalanche metrics (exponents, statistics) from code/analysis/fitting.py
- Quality control status from code/data/quality_control.py

Output: data/results/metrics_export.csv
"""
import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_data_root, ensure_directories
from utils.logger import get_logger, ResearchError
from analysis.metrics import run_metrics_pipeline
from analysis.fitting import run_fitting_pipeline
from data.quality_control import run_qc_for_subject, calculate_pipeline_completeness
from data.store import load_connectome_matrix, load_eeg_time_series

logger = get_logger(__name__)

def load_metrics_from_store(subject_id: str, data_root: Path) -> Optional[Dict[str, Any]]:
    """Load computed structural metrics for a subject from JSON store."""
    metrics_path = data_root / "processed" / "metrics" / f"{subject_id}_metrics.json"
    if not metrics_path.exists():
        logger.warning(f"Metrics file not found for subject {subject_id}: {metrics_path}")
        return None
    
    try:
        with open(metrics_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load metrics for {subject_id}: {e}")
        return None

def load_avalanche_fitting_results(subject_id: str, data_root: Path) -> Optional[Dict[str, Any]]:
    """Load computed avalanche fitting results for a subject from JSON store."""
    fitting_path = data_root / "processed" / "avalanches" / f"{subject_id}_fitting.json"
    if not fitting_path.exists():
        logger.warning(f"Fitting results not found for subject {subject_id}: {fitting_path}")
        return None
    
    try:
        with open(fitting_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load fitting results for {subject_id}: {e}")
        return None

def load_qc_status(subject_id: str, data_root: Path) -> Dict[str, Any]:
    """Load QC status for a subject."""
    qc_path = data_root / "processed" / "qc" / f"{subject_id}_qc.json"
    default_status = {
        "passed": False,
        "snr": None,
        "is_connected": None,
        "reason": "No QC data found"
    }
    
    if not qc_path.exists():
        return default_status
    
    try:
        with open(qc_path, 'r') as f:
            qc_data = json.load(f)
            return {
                "passed": qc_data.get("passed", False),
                "snr": qc_data.get("mean_snr"),
                "is_connected": qc_data.get("is_connected"),
                "reason": qc_data.get("reason", "Unknown")
            }
    except Exception as e:
        logger.error(f"Failed to load QC data for {subject_id}: {e}")
        return default_status

def collect_subject_metrics(subject_id: str, data_root: Path) -> Dict[str, Any]:
    """Collect all metrics for a single subject into a flat dictionary."""
    metrics_data = load_metrics_from_store(subject_id, data_root)
    fitting_data = load_avalanche_fitting_results(subject_id, data_root)
    qc_data = load_qc_status(subject_id, data_root)
    
    row = {
        "subject_id": subject_id,
        "qc_passed": qc_data["passed"],
        "mean_snr": qc_data["snr"],
        "is_connected": qc_data["is_connected"],
        "qc_reason": qc_data["reason"]
    }
    
    if metrics_data:
        row["degree_centrality_mean"] = metrics_data.get("mean_degree_centrality")
        row["degree_centrality_std"] = metrics_data.get("std_degree_centrality")
        row["clustering_coeff_mean"] = metrics_data.get("mean_clustering_coefficient")
        row["clustering_coeff_std"] = metrics_data.get("std_clustering_coefficient")
        row["rich_club_coeff"] = metrics_data.get("rich_club_coefficient")
    else:
        row["degree_centrality_mean"] = None
        row["degree_centrality_std"] = None
        row["clustering_coeff_mean"] = None
        row["clustering_coeff_std"] = None
        row["rich_club_coeff"] = None
    
    if fitting_data:
        row["avalanche_size_exponent"] = fitting_data.get("exponent")
        row["avalanche_duration_exponent"] = fitting_data.get("duration_exponent")
        row["power_law_p_value"] = fitting_data.get("p_value")
        row["power_law_log_likelihood"] = fitting_data.get("log_likelihood")
        row["best_model"] = fitting_data.get("best_model")
        row["n_avalanches"] = fitting_data.get("n_avalanches")
    else:
        row["avalanche_size_exponent"] = None
        row["avalanche_duration_exponent"] = None
        row["power_law_p_value"] = None
        row["power_law_log_likelihood"] = None
        row["best_model"] = None
        row["n_avalanches"] = None
    
    return row

def run_export_pipeline(subject_ids: Optional[List[str]] = None, output_path: Optional[Path] = None) -> Path:
    """
    Run the export pipeline to generate the participant-level CSV.
    
    Args:
        subject_ids: List of subject IDs to process. If None, uses all found in data/processed.
        output_path: Optional path for the output CSV. Defaults to data/results/metrics_export.csv.
    
    Returns:
        Path to the generated CSV file.
    """
    data_root = get_data_root()
    ensure_directories()
    
    if output_path is None:
        output_path = data_root / "results" / "metrics_export.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine subject IDs
    if subject_ids is None:
        # Find all subject folders in data/processed/connectomes or data/processed/eeg
        connectome_dir = data_root / "processed" / "connectomes"
        eeg_dir = data_root / "processed" / "eeg"
        
        subject_ids = set()
        if connectome_dir.exists():
            for item in connectome_dir.iterdir():
                if item.is_dir() and item.name.startswith("sub-"):
                    subject_ids.add(item.name)
        if eeg_dir.exists():
            for item in eeg_dir.iterdir():
                if item.is_dir() and item.name.startswith("sub-"):
                    subject_ids.add(item.name)
        
        subject_ids = sorted(list(subject_ids))
        logger.info(f"Discovered {len(subject_ids)} subjects from data directory")
    
    if not subject_ids:
        raise ResearchError("No subjects found to export metrics for.")
    
    rows = []
    for subject_id in subject_ids:
        try:
            logger.info(f"Collecting metrics for {subject_id}")
            row = collect_subject_metrics(subject_id, data_root)
            rows.append(row)
        except Exception as e:
            logger.error(f"Failed to collect metrics for {subject_id}: {e}")
            # Still add a row with nulls for failed subjects to track progress
            rows.append({
                "subject_id": subject_id,
                "error": str(e)
            })
    
    df = pd.DataFrame(rows)
    
    # Sort by subject_id
    df = df.sort_values("subject_id")
    
    # Reorder columns for readability
    column_order = [
        "subject_id", "qc_passed", "mean_snr", "is_connected", "qc_reason",
        "degree_centrality_mean", "degree_centrality_std",
        "clustering_coeff_mean", "clustering_coeff_std", "rich_club_coeff",
        "avalanche_size_exponent", "avalanche_duration_exponent",
        "power_law_p_value", "power_law_log_likelihood", "best_model", "n_avalanches"
    ]
    
    # Filter to only columns that exist in df
    final_columns = [c for c in column_order if c in df.columns]
    # Append any remaining columns not in the standard order
    remaining = [c for c in df.columns if c not in final_columns]
    final_columns.extend(remaining)
    
    df = df[final_columns]
    df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully exported metrics for {len(rows)} subjects to {output_path}")
    logger.info(f"Summary: {df['qc_passed'].sum() if 'qc_passed' in df.columns else 0} subjects passed QC")
    
    return output_path

def main():
    """Entry point for the export script."""
    logger.info("Starting metrics export pipeline")
    try:
        output_path = run_export_pipeline()
        logger.info(f"Export completed. Output: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Export pipeline failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
