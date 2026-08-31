import os
import sys
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from utils as per API surface
from utils import setup_logging, get_logger

def load_instructional_units(input_path: str) -> List[Dict[str, Any]]:
    """
    Load instructional units from a CSV file.
    
    Args:
        input_path: Path to the instructional_units.csv file.
        
    Returns:
        List of dictionaries containing the instructional units.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or lacks required columns.
    """
    import pandas as pd
    
    logger = get_logger()
    logger.info(f"Loading instructional units from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if df.empty:
        raise ValueError("Input file is empty.")
    
    required_cols = ['unit_id', 'text']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    units = df.to_dict('records')
    logger.info(f"Loaded {len(units)} instructional units")
    return units

def normalize_text(text: str) -> str:
    """
    Apply minimal stylistic normalization to the text.
    
    This function preserves the original text content but cleans up:
    - Multiple consecutive spaces
    - Leading/trailing whitespace
    - Inconsistent line breaks
    
    Args:
        text: The original text string.
        
    Returns:
        Normalized text string.
    """
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize line breaks (keep single newlines, remove excessive ones)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

def generate_moderate_tier(unit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the Moderate (baseline) tier for a single instructional unit.
    
    The Moderate tier preserves the original text or applies minimal
    stylistic normalization. It serves as the baseline for comparison
    with Simple and Complex tiers.
    
    Args:
        unit: Dictionary containing 'unit_id' and 'text'.
        
    Returns:
        Dictionary with 'unit_id', 'original_text', 'moderate_text', and 'tier'.
    """
    unit_id = unit.get('unit_id', '')
    original_text = unit.get('text', '')
    
    moderate_text = normalize_text(original_text)
    
    return {
        'unit_id': unit_id,
        'original_text': original_text,
        'moderate_text': moderate_text,
        'tier': 'moderate'
    }

def save_moderate_tiers(tiers: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the generated moderate tiers to a CSV file.
    
    Args:
        tiers: List of dictionaries containing tier data.
        output_path: Path to the output CSV file.
        
    Raises:
        ValueError: If the tiers list is empty.
    """
    import pandas as pd
    
    logger = get_logger()
    
    if not tiers:
        raise ValueError("No tiers to save.")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    df = pd.DataFrame(tiers)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(tiers)} moderate tiers to {output_path}")

def main() -> None:
    """
    Main entry point for generating the Moderate tier.
    
    Reads from data/processed/instructional_units.csv and writes
    to data/explanation_tiers/moderate_tiers.csv.
    """
    setup_logging()
    logger = get_logger()
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "processed" / "instructional_units.csv"
    output_path = project_root / "data" / "explanation_tiers" / "moderate_tiers.csv"
    
    try:
        # Load instructional units
        units = load_instructional_units(str(input_path))
        
        # Generate moderate tiers
        moderate_tiers = []
        for unit in units:
            tier = generate_moderate_tier(unit)
            moderate_tiers.append(tier)
        
        # Save results
        save_moderate_tiers(moderate_tiers, str(output_path))
        
        logger.info("Moderate tier generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
