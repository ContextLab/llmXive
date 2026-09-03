import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from code.config import PROCESSED_PATH, get_logger

logger = get_logger(__name__)

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns None if the file does not exist or is invalid.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None

def check_significance(system_data: Dict[str, Any], p_threshold: float = 0.05, coeff_threshold: float = 0.01) -> bool:
    """
    Check if a system has significant cooperative effects.
    
    Criteria:
    1. At least one interaction term has p-value < p_threshold
    2. The absolute value of that coefficient is > coeff_threshold (eV)
    
    Returns:
        True if significant effects are detected, False otherwise.
    """
    interaction_results = system_data.get("interaction_terms", {})
    if not interaction_results:
        logger.warning(f"No interaction term data found for system. Marking as non-significant.")
        return False

    significant_found = False
    for term, stats in interaction_results.items():
        p_value = stats.get("p_value")
        coefficient = stats.get("coefficient")
        
        if p_value is None or coefficient is None:
            continue

        if p_value < p_threshold and abs(coefficient) > coeff_threshold:
            significant_found = True
            logger.debug(f"Significant interaction found for {term}: p={p_value:.4f}, coeff={coefficient:.4f}")
            break

    return significant_found

def run_flagging_logic(cooperative_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the cooperative effects data and flag systems where no significant 
    cooperative effects are detected within statistical power.
    
    Args:
        cooperative_data: The full data structure from cooperative_effects_analysis.json.
    
    Returns:
        A dictionary containing the original data plus a 'flagged_systems' list.
    """
    flagged_systems = []
    systems = cooperative_data.get("systems", [])
    
    if not systems:
        logger.warning("No systems found in cooperative effects data.")
        return cooperative_data

    for system in systems:
        system_name = system.get("system_name", "Unknown")
        is_significant = check_significance(system)
        
        if not is_significant:
            flagged_systems.append({
                "system_name": system_name,
                "reason": "No significant cooperative effects detected (p >= 0.05 or |coeff| <= 0.01 eV)",
                "status": "non_significant"
            })
            logger.info(f"System {system_name} flagged: No significant cooperative effects.")
        else:
            logger.info(f"System {system_name} passed significance check.")

    cooperative_data["flagged_systems"] = flagged_systems
    cooperative_data["summary"] = {
        "total_systems": len(systems),
        "significant_systems": len(systems) - len(flagged_systems),
        "non_significant_systems": len(flagged_systems)
    }
    
    return cooperative_data

def main():
    input_path = PROCESSED_PATH / "cooperative_effects_analysis.json"
    output_path = PROCESSED_PATH / "cooperative_effects_analysis.json"
    
    logger.info(f"Loading cooperative effects data from {input_path}")
    data = load_json_safe(input_path)
    
    if data is None:
        logger.error("Failed to load input data. Exiting.")
        sys.exit(1)
    
    logger.info("Running flagging logic for non-significant systems...")
    updated_data = run_flagging_logic(data)
    
    logger.info(f"Saving updated analysis to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(updated_data, f, indent=2)
    
    logger.info(f"Flagging complete. {updated_data['summary']['non_significant_systems']} systems flagged as non-significant.")

if __name__ == "__main__":
    main()