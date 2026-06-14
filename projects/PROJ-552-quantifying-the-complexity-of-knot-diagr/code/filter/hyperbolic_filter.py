"""Filter dataset to hyperbolic knots (volume > 0) and log excluded knots.

This module implements FR-012 filtering requirement and SC-012 verification
by excluding non-hyperbolic knots (volume <= 0) and documenting all exclusions.
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

from reproducibility.logs import log_operation, get_logger

# Set up logger for reproducibility tracking
logger = get_logger(__name__)

# Constants
HYPERBOLIC_VOLUME_THRESHOLD = 0.0
CLEANED_DATA_PATH = Path("data/processed/knots_cleaned.csv")
FILTERED_DATA_PATH = Path("data/processed/knots_hyperbolic.csv")
EXCLUDED_LOG_PATH = Path("docs/reproducibility/excluded_knots.md")
EXCLUSION_COUNT_PATH = Path("docs/reproducibility/exclusion_count.json")

def load_cleaned_knots(filepath: Path) -> List[Dict[str, Any]]:
    """Load cleaned knots from CSV file.
    
    Args:
        filepath: Path to cleaned knots CSV file.
        
    Returns:
        List of knot records as dictionaries.
    """
    knots = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            knots.append(row)
    return knots

def parse_hyperbolic_volume(volume_str: str) -> float:
    """Parse hyperbolic volume string to float.
    
    Args:
        volume_str: Volume value as string.
        
    Returns:
        Parsed float value, or 0.0 if missing/invalid.
    """
    if volume_str is None or volume_str == '' or volume_str == 'null':
        return 0.0
    try:
        return float(volume_str)
    except (ValueError, TypeError):
        return 0.0

def filter_hyperbolic_knots(knots: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Filter knots to only those with hyperbolic volume > 0.
    
    Per FR-012, exclude knots that are not hyperbolic (volume <= 0).
    This includes non-hyperbolic knots (volume = 0) and knots with missing volume data.
    
    Args:
        knots: List of knot records to filter.
        
    Returns:
        Tuple of (hyperbolic_knots, excluded_knots).
    """
    hyperbolic = []
    excluded = []
    
    for knot in knots:
        volume = parse_hyperbolic_volume(knot.get('hyperbolic_volume', ''))
        
        if volume > HYPERBOLIC_VOLUME_THRESHOLD:
            hyperbolic.append(knot)
        else:
            # Determine exclusion reason
            original_volume = knot.get('hyperbolic_volume', '')
            if original_volume is None or original_volume == '' or original_volume == 'null':
                reason = "missing_volume"
            elif volume == 0.0:
                reason = "non_hyperbolic_volume_zero"
            else:
                reason = "non_hyperbolic_volume_negative"
            
            excluded_knot = dict(knot)
            excluded_knot['exclusion_reason'] = reason
            excluded_knot['exclusion_volume'] = original_volume
            excluded.append(excluded_knot)
    
    return hyperbolic, excluded

def save_filtered_knots(knots: List[Dict[str, Any]], filepath: Path) -> None:
    """Save filtered hyperbolic knots to CSV file.
    
    Args:
        knots: List of hyperbolic knot records.
        filepath: Output path for filtered CSV.
    """
    if not knots:
        logger.warning(f"No hyperbolic knots to save at {filepath}")
        return
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(knots[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(knots)

def log_excluded_knots(excluded_knots: List[Dict[str, Any]], output_path: Path) -> None:
    """Log excluded knots to markdown file for reproducibility.
    
    Per SC-012, this documentation enables verification that exclusion count
    matches the actual number of excluded knots.
    
    Args:
        excluded_knots: List of excluded knot records with reasons.
        output_path: Path to output markdown file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Excluded Knots Report\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total excluded knots: {len(excluded_knots)}\n\n")
        
        # Count by exclusion reason
        reason_counts: Dict[str, int] = {}
        for knot in excluded_knots:
            reason = knot.get('exclusion_reason', 'unknown')
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        f.write("### Exclusion Breakdown\n\n")
        for reason, count in sorted(reason_counts.items()):
            f.write(f"- {reason}: {count}\n")
        f.write("\n")
        
        if excluded_knots:
            f.write("## Excluded Knot Details\n\n")
            f.write("| Knot ID | Crossing Number | Original Volume | Exclusion Reason |\n")
            f.write("|---------|-----------------|-----------------|------------------|\n")
            
            for knot in excluded_knots:
                knot_id = knot.get('knot_id', knot.get('id', 'N/A'))
                crossing = knot.get('crossing_number', 'N/A')
                volume = knot.get('exclusion_volume', 'N/A')
                reason = knot.get('exclusion_reason', 'unknown')
                
                f.write(f"| {knot_id} | {crossing} | {volume} | {reason} |\n")
        
        f.write("\n## Exclusion Criteria\n\n")
        f.write("Knots were excluded based on the following criteria (per FR-012):\n\n")
        f.write("- **Non-hyperbolic knots**: Hyperbolic volume = 0 (toroidal or satellite knots)\n")
        f.write("- **Missing data**: Hyperbolic volume field is null, empty, or unparseable\n")
        f.write("- **Invalid data**: Hyperbolic volume is negative (mathematically impossible)\n\n")
        
        f.write("## Verification\n\n")
        f.write(f"Exclusion count: **{len(excluded_knots)}**\n\n")
        f.write("This count should match the number of excluded records logged above.\n")
        f.write("Per SC-012, verify that the exclusion count in this document matches\n")
        f.write("the actual number of excluded knots in the filtered dataset.\n")

def save_exclusion_count(excluded_knots: List[Dict[str, Any]], output_path: Path) -> None:
    """Save exclusion count to JSON for automated verification.
    
    Args:
        excluded_knots: List of excluded knot records.
        output_path: Path to output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    count_data = {
        "total_excluded": len(excluded_knots),
        "timestamp": get_logger().get_current_timestamp() if hasattr(get_logger(), 'get_current_timestamp') else "N/A"
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(count_data, f, indent=2)

def verify_exclusion_count(md_path: Path, json_path: Path) -> bool:
    """Verify exclusion count matches between markdown and JSON files.
    
    Per SC-012 verification requirement.
    
    Args:
        md_path: Path to excluded_knots.md.
        json_path: Path to exclusion_count.json.
        
    Returns:
        True if counts match, False otherwise.
    """
    try:
        # Read JSON count
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        json_count = json_data.get('total_excluded', 0)
        
        # Read markdown count (parse from summary line)
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Simple parsing of the markdown summary
        import re
        match = re.search(r'Total excluded knots:\s*(\d+)', md_content)
        if not match:
            logger.error("Could not find exclusion count in markdown file")
            return False
        
        md_count = int(match.group(1))
        
        if md_count != json_count:
            logger.error(f"Count mismatch: markdown={md_count}, json={json_count}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

def main() -> None:
    """Main entry point for hyperbolic knot filtering."""
    log_operation(
        operation="filter_hyperbolic_knots",
        input_file=str(CLEANED_DATA_PATH),
        output_files=[str(FILTERED_DATA_PATH), str(EXCLUDED_LOG_PATH), str(EXCLUSION_COUNT_PATH)],
        parameters={"volume_threshold": HYPERBOLIC_VOLUME_THRESHOLD}
    )
    
    # Load cleaned data
    logger.info(f"Loading cleaned knots from {CLEANED_DATA_PATH}")
    cleaned_knots = load_cleaned_knots(CLEANED_DATA_PATH)
    total_count = len(cleaned_knots)
    logger.info(f"Loaded {total_count} cleaned knots")
    
    # Filter to hyperbolic knots
    logger.info("Filtering to hyperbolic knots (volume > 0)")
    hyperbolic_knots, excluded_knots = filter_hyperbolic_knots(cleaned_knots)
    
    # Log results
    hyperbolic_count = len(hyperbolic_knots)
    excluded_count = len(excluded_knots)
    logger.info(f"Filtered results: {hyperbolic_count} hyperbolic, {excluded_count} excluded")
    
    # Save filtered data
    logger.info(f"Saving hyperbolic knots to {FILTERED_DATA_PATH}")
    save_filtered_knots(hyperbolic_knots, FILTERED_DATA_PATH)
    
    # Log excluded knots
    logger.info(f"Logging excluded knots to {EXCLUDED_LOG_PATH}")
    log_excluded_knots(excluded_knots, EXCLUDED_LOG_PATH)
    
    # Save exclusion count for verification
    logger.info(f"Saving exclusion count to {EXCLUSION_COUNT_PATH}")
    save_exclusion_count(excluded_knots, EXCLUSION_COUNT_PATH)
    
    # Verify counts match
    logger.info("Verifying exclusion count consistency")
    if verify_exclusion_count(EXCLUDED_LOG_PATH, EXCLUSION_COUNT_PATH):
        logger.info("Exclusion count verification PASSED")
    else:
        logger.error("Exclusion count verification FAILED")
    
    # Log completion
    log_operation(
        operation="filter_hyperbolic_knots_complete",
        input_file=str(CLEANED_DATA_PATH),
        output_files=[str(FILTERED_DATA_PATH), str(EXCLUDED_LOG_PATH), str(EXCLUSION_COUNT_PATH)],
        parameters={
            "total_knots": total_count,
            "hyperbolic_count": hyperbolic_count,
            "excluded_count": excluded_count
        },
        status="success"
    )
    
    logger.info("Hyperbolic knot filtering complete")

if __name__ == "__main__":
    main()
