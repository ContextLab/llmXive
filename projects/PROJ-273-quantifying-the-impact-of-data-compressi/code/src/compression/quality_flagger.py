"""
Compression Quality Flagging Module (US2 - T023)

Implements logic to flag compression levels with SNR degradation > 5%
as 'unacceptable' according to FR-002, FR-003, FR-004, and SC-002.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from src.utils.logging import get_logger
from src.utils.config import get_project_root, ensure_dir

logger = get_logger(__name__)

# Threshold for unacceptable SNR degradation (5%)
SNR_DEGRADATION_THRESHOLD = 5.0

def flag_compression_quality(
    metrics_data: Dict[str, Any],
    threshold: float = SNR_DEGRADATION_THRESHOLD
) -> Dict[str, Any]:
    """
    Analyze compression metrics and flag levels with SNR degradation > threshold.
    
    Args:
        metrics_data: Dictionary containing compression metrics for an event.
                     Expected structure:
                     {
                         "event_id": str,
                         "compression_results": [
                             {
                                 "method": str,
                                 "level": str|int,
                                 "snr_degradation_db": float,
                                 "mse": float,
                                 ...
                             },
                             ...
                         ]
                     }
        threshold: SNR degradation threshold in dB above which a level is unacceptable.
    
    Returns:
        Dictionary with original data plus a 'quality_flags' section containing:
        - "unacceptable_levels": List of (method, level) tuples that exceeded threshold
        - "acceptable_levels": List of (method, level) tuples that passed
        - "summary": Count of acceptable vs unacceptable
    """
    if not metrics_data or "compression_results" not in metrics_data:
        logger.warning("Invalid metrics data structure provided")
        return {
            "quality_flags": {
                "unacceptable_levels": [],
                "acceptable_levels": [],
                "summary": {"acceptable": 0, "unacceptable": 0}
            }
        }
    
    results = metrics_data.get("compression_results", [])
    unacceptable = []
    acceptable = []
    
    for result in results:
        method = result.get("method", "unknown")
        level = result.get("level", "unknown")
        snr_degradation = result.get("snr_degradation_db", 0.0)
        
        if snr_degradation > threshold:
            unacceptable.append({
                "method": method,
                "level": level,
                "snr_degradation_db": snr_degradation,
                "reason": f"SNR degradation ({snr_degradation:.2f} dB) exceeds threshold ({threshold} dB)"
            })
        else:
            acceptable.append({
                "method": method,
                "level": level,
                "snr_degradation_db": snr_degradation
            })
    
    return {
        "event_id": metrics_data.get("event_id"),
        "quality_flags": {
            "unacceptable_levels": unacceptable,
            "acceptable_levels": acceptable,
            "summary": {
                "acceptable": len(acceptable),
                "unacceptable": len(unacceptable),
                "total": len(results)
            }
        }
    }

def process_quality_flags_for_event(
    metrics_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Process metrics for a single event and save quality flags.
    
    Args:
        metrics_path: Path to the JSON file containing compression metrics
        output_path: Path where the flagged results will be saved
    
    Returns:
        The flagged results dictionary
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        metrics_data = json.load(f)
    
    flagged_data = flag_compression_quality(metrics_data)
    
    # Ensure output directory exists
    ensure_dir(output_path)
    
    with open(output_path, 'w') as f:
        json.dump(flagged_data, f, indent=2)
    
    logger.info(f"Quality flags saved to {output_path}")
    logger.info(
        f"Summary: {flagged_data['quality_flags']['summary']['acceptable']} "
        f"acceptable, {flagged_data['quality_flags']['summary']['unacceptable']} unacceptable"
    )
    
    return flagged_data

def aggregate_quality_report(
    metrics_dir: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Aggregate quality flags across all events in a directory.
    
    Args:
        metrics_dir: Directory containing metrics JSON files for multiple events
        output_path: Path where the aggregated report will be saved
    
    Returns:
        Aggregated report dictionary
    """
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    
    all_flags = []
    total_acceptable = 0
    total_unacceptable = 0
    
    for metrics_file in metrics_dir.glob("*.json"):
        try:
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
            
            flagged = flag_compression_quality(metrics_data)
            all_flags.append(flagged)
            
            summary = flagged["quality_flags"]["summary"]
            total_acceptable += summary["acceptable"]
            total_unacceptable += summary["unacceptable"]
            
        except Exception as e:
            logger.error(f"Error processing {metrics_file}: {e}")
            continue
    
    report = {
        "total_events_processed": len(all_flags),
        "total_compression_tests": total_acceptable + total_unacceptable,
        "overall_summary": {
            "acceptable": total_acceptable,
            "unacceptable": total_unacceptable,
            "acceptance_rate": (
                total_acceptable / (total_acceptable + total_unacceptable) 
                if (total_acceptable + total_unacceptable) > 0 
                else 0.0
            )
        },
        "per_event_flags": all_flags
    }
    
    ensure_dir(output_path)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Aggregated quality report saved to {output_path}")
    logger.info(
        f"Overall acceptance rate: {report['overall_summary']['acceptance_rate']:.2%}"
    )
    
    return report

def main():
    """
    Main entry point for quality flagging.
    Processes metrics from data/interim/compression_metrics/ 
    and outputs flags to data/processed/quality_flags.json
    """
    project_root = get_project_root()
    
    # Default paths
    metrics_dir = project_root / "data" / "interim" / "compression_metrics"
    output_file = project_root / "data" / "processed" / "quality_flags.json"
    
    # Check if metrics directory exists
    if not metrics_dir.exists():
        logger.error(f"Metrics directory not found: {metrics_dir}")
        logger.error("Please run src/compression/main.py first to generate metrics.")
        return 1
    
    try:
        report = aggregate_quality_report(metrics_dir, output_file)
        logger.info("Quality flagging completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Quality flagging failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
