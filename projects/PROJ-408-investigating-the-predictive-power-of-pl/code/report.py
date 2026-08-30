import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import get_config

logger = logging.getLogger("report")

def append_validation_log(message: str) -> None:
    """
    Appends a message to the validation log file.
    Ensures the output directory exists before writing.
    """
    config = get_config()
    log_path = Path(config.output_dir) / "reports" / "validation_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    
    logger.info(f"Validation log updated: {message}")

def verify_sc003_retention(total_species: int, retained_species: int) -> bool:
    """
    Verifies SC-003: Retention threshold compliance.
    
    Logic:
    1. Calculate final retention percentage: (retained / total) * 100.
    2. Compare against the target threshold (defined in config, default 80%).
    3. Append status "SC-003: Retention X% (PASS/FAIL)" to validation_log.txt.
    
    Args:
        total_species: Total number of species requested.
        retained_species: Number of species with both data types.
        
    Returns:
        True if retention passes threshold, False otherwise.
    """
    config = get_config()
    threshold = config.retention_threshold_percent
    
    if total_species == 0:
        retention_pct = 0.0
        passed = False
    else:
        retention_pct = (retained_species / total_species) * 100
        passed = retention_pct >= threshold
    
    status = "PASS" if passed else "FAIL"
    message = f"SC-003: Retention {retention_pct:.1f}% (Threshold: {threshold}%) -> {status}"
    
    append_validation_log(message)
    
    if not passed:
        logger.warning(f"SC-003 Check Failed: {retention_pct:.1f}% < {threshold}%")
    
    return passed

def generate_analysis_summary(results: Dict[str, Any]) -> None:
    """
    Generates the final analysis summary text file.
    
    Args:
        results: Dictionary containing mantel_r, mantel_p, partial_r, etc.
    """
    config = get_config()
    summary_path = Path(config.output_dir) / "reports" / "analysis_summary.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=== Phylogenetic Signal Analysis Summary ===\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        if "mantel_r" in results:
            f.write(f"Mantel Correlation (r): {results['mantel_r']:.4f}\n")
        if "mantel_p" in results:
            f.write(f"Mantel P-value: {results['mantel_p']:.4f}\n")
        if "partial_r" in results:
            f.write(f"Partial Mantel Correlation (r): {results['partial_r']:.4f}\n")
        if "partial_p" in results:
            f.write(f"Partial Mantel P-value: {results['partial_p']:.4f}\n")
        
        if "mantel_r" in results and "partial_r" in results:
            if results['mantel_r'] != 0:
                ratio = results['partial_r'] / results['mantel_r']
                f.write(f"Robustness Ratio (Partial/Standard): {ratio:.4f}\n")
        
        f.write("\n=== End of Summary ===\n")
    
    logger.info(f"Analysis summary generated: {summary_path}")
