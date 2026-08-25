"""
Reporting module for the phylogeny-metabolite prediction pipeline.
Handles validation checks, result aggregation, and log generation.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import get_config

logger = logging.getLogger(__name__)

def append_validation_log(log_path: Path, message: str) -> None:
    """
    Appends a timestamped message to the validation log file.
    Ensures the directory exists before writing.
    
    Args:
        log_path: Path to the validation log file.
        message: The message string to append.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    logger.info(f"Validation log updated: {log_path}")

def verify_sc003_retention(
    total_target_species: int,
    retained_species: int,
    threshold: float = 0.80,
    log_path: Optional[Path] = None
) -> bool:
    """
    Verifies SC-003: Data Retention Threshold.
    
    Calculates the retention percentage (species with both data types / total target)
    and compares it against the configured threshold.
    
    Args:
        total_target_species: Total number of species requested/targeted.
        retained_species: Number of species that successfully retained both 
                          sequence and metabolite data.
        threshold: Minimum retention ratio required (default 0.80 for 80%).
        log_path: Path to append the validation status. If None, uses config default.
    
    Returns:
        bool: True if retention >= threshold, False otherwise.
    
    Raises:
        ValueError: If total_target_species is 0.
    """
    if total_target_species == 0:
        logger.error("SC-003 Check failed: Total target species is 0.")
        return False
    
    retention_ratio = retained_species / total_target_species
    retention_percent = retention_ratio * 100
    
    # Determine pass/fail
    passed = retention_ratio >= threshold
    status = "PASS" if passed else "FAIL"
    
    # Format message
    message = f"SC-003: Retention {retention_percent:.1f}% ({status})"
    
    # Log to file
    if log_path is None:
        config = get_config()
        log_path = Path(config.output_dir) / "reports" / "validation_log.txt"
    
    append_validation_log(log_path, message)
    
    logger.info(message)
    
    return passed

def generate_analysis_summary(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generates a text summary of the analysis results.
    
    Args:
        results: Dictionary containing Mantel stats, partial Mantel stats, etc.
        output_path: Path where the summary file will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "Phylogeny-Metabolite Prediction Analysis Summary",
        "=" * 50,
        f"Generated: {datetime.now().isoformat()}",
        ""
    ]
    
    # Mantel Results
    if 'mantel_r' in results:
        lines.append(f"Mantel Correlation (r): {results['mantel_r']:.4f}")
    if 'mantel_p' in results:
        lines.append(f"Mantel P-value: {results['mantel_p']:.4f}")
    
    # Partial Mantel Results
    if 'partial_mantel_r' in results:
        lines.append(f"Partial Mantel Correlation (r): {results['partial_mantel_r']:.4f}")
    if 'partial_mantel_p' in results:
        lines.append(f"Partial Mantel P-value: {results['partial_mantel_p']:.4f}")
    
    # Robustness Check (SC-002)
    if 'mantel_r' in results and 'partial_mantel_r' in results:
        ratio = results['partial_mantel_r'] / results['mantel_r'] if results['mantel_r'] != 0 else 0
        lines.append(f"Robustness Ratio (Partial/Standard r): {ratio:.4f}")
    
    # Retention Stats
    if 'retention_percent' in results:
        lines.append(f"Data Retention: {results['retention_percent']:.1f}%")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Analysis summary saved to {output_path}")