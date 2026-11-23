import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import get_config
import json

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
    3. Append status "SC-003: Retention X% (Threshold: Y%) -> PASS/FAIL" to validation_log.txt.
    
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

def _load_json_safely(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None if missing or invalid."""
    if not path.exists():
        logger.warning(f"JSON file not found: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load JSON {path}: {e}")
        return None

def generate_analysis_summary(results: Optional[Dict[str, Any]] = None) -> None:
    """
    Generates the final analysis summary text file.
    
    Reads results from disk if not provided in memory:
    - Standard Mantel: data/processed/mantel_results.json
    - Partial Mantel: data/processed/partial_mantel_results.json
    
    Args:
        results: Optional dictionary containing pre-loaded results.
                 If None, loads from standard paths.
    """
    config = get_config()
    data_dir = Path(config.data_dir)
    output_dir = Path(config.output_dir)
    
    # Load results if not provided
    if results is None:
        results = {}
        
        # Load Standard Mantel
        mantel_path = data_dir / "processed" / "mantel_results.json"
        mantel_data = _load_json_safely(mantel_path)
        if mantel_data:
            if "r" in mantel_data: results["mantel_r"] = mantel_data["r"]
            if "p_value" in mantel_data: results["mantel_p"] = mantel_data["p_value"]
            elif "p" in mantel_data: results["mantel_p"] = mantel_data["p"]
        
        # Load Partial Mantel
        partial_path = data_dir / "processed" / "partial_mantel_results.json"
        partial_data = _load_json_safely(partial_path)
        if partial_data:
            if "partial_r" in partial_data: results["partial_r"] = partial_data["partial_r"]
            elif "r" in partial_data: results["partial_r"] = partial_data["r"]
            if "partial_p" in partial_data: results["partial_p"] = partial_data["partial_p"]
            elif "p" in partial_data and "partial_r" in partial_data: results["partial_p"] = partial_data["p"]
    
    summary_path = output_dir / "reports" / "analysis_summary.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=== Phylogenetic Signal Analysis Summary ===\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        # Standard Mantel
        if "mantel_r" in results:
            f.write(f"Mantel Correlation (r): {results['mantel_r']:.4f}\n")
        else:
            f.write("Mantel Correlation (r): N/A\n")
            
        if "mantel_p" in results:
            f.write(f"Mantel P-value: {results['mantel_p']:.4f}\n")
        else:
            f.write("Mantel P-value: N/A\n")
        
        # Partial Mantel
        if "partial_r" in results:
            f.write(f"Partial Mantel Correlation (r): {results['partial_r']:.4f}\n")
        else:
            f.write("Partial Mantel Correlation (r): N/A\n")
            
        if "partial_p" in results:
            f.write(f"Partial Mantel P-value: {results['partial_p']:.4f}\n")
        else:
            f.write("Partial Mantel P-value: N/A\n")
        
        # Robustness Ratio (Partial / Standard) per SC-002
        if "mantel_r" in results and "partial_r" in results:
            std_r = results['mantel_r']
            if std_r != 0:
                ratio = results['partial_r'] / std_r
                f.write(f"Robustness Ratio (Partial/Standard): {ratio:.4f}\n")
            else:
                f.write("Robustness Ratio (Partial/Standard): Undefined (Standard r is 0)\n")
        else:
            f.write("Robustness Ratio (Partial/Standard): Cannot calculate (missing data)\n")
        
        f.write("\n=== End of Summary ===\n")
    
    logger.info(f"Analysis summary generated: {summary_path}")