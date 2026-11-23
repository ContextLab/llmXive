import os
import sys
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure code/ is in path for relative imports if run as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from utils import get_logger

logger = get_logger(__name__)

def load_instructional_units(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads instructional units from a CSV file.
    Expected columns: 'unit_id', 'text' (or similar).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Instructional units file not found: {input_path}")
    
    df = None
    try:
        import pandas as pd
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV {input_path}: {e}")
        raise

    # Normalize column names to lowercase for flexibility
    df.columns = df.columns.str.lower().str.strip()
    
    required_cols = ['unit_id', 'text']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    units = df.to_dict(orient='records')
    logger.info(f"Loaded {len(units)} instructional units from {input_path}")
    return units

def normalize_text(text: str) -> str:
    """
    Applies minimal stylistic normalization to the text.
    - Removes excessive whitespace.
    - Ensures standard punctuation spacing.
    - Fixes common encoding artifacts if present.
    Preserves the original meaning and complexity.
    """
    if not isinstance(text, str):
        return str(text)
    
    # Collapse multiple spaces/newlines into single space
    text = re.sub(r'\s+', ' ', text)
    
    # Fix punctuation spacing (e.g., "word ." -> "word.")
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    # Ensure space after punctuation if missing (e.g., "word,word" -> "word, word")
    # But be careful not to break decimals or abbreviations if possible.
    # Simple heuristic: add space after punctuation if next char is alpha.
    text = re.sub(r'([.,;:!?])([a-zA-Z])', r'\1 \2', text)
    
    return text.strip()

def generate_moderate_tier(unit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates the 'Moderate' tier for a single instructional unit.
    Strategy: Preserve original text with minimal normalization.
    """
    original_text = unit.get('text', '')
    normalized_text = normalize_text(original_text)
    
    return {
        'unit_id': unit['unit_id'],
        'tier': 'moderate',
        'text': normalized_text,
        'source': 'original'
    }

def save_moderate_tiers(tiers: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the generated moderate tiers to a CSV file.
    """
    if not tiers:
        logger.warning("No tiers to save.")
        return
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import pandas as pd
    df = pd.DataFrame(tiers)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(tiers)} moderate tiers to {output_path}")

def main():
    """
    Main entry point for generating the moderate tier.
    Reads from data/processed/instructional_units.csv
    Writes to data/explanation_tiers/moderate_tiers.csv
    """
    input_path = "data/processed/instructional_units.csv"
    output_path = "data/explanation_tiers/moderate_tiers.csv"
    
    logger.info(f"Starting moderate tier generation from {input_path}")
    
    try:
        units = load_instructional_units(input_path)
    except FileNotFoundError as e:
        logger.critical(str(e))
        logger.critical("HINT: Ensure T022 (Extract Instructional Units) has been run successfully.")
        sys.exit(1)
    
    if not units:
        logger.error("No instructional units found in input file.")
        sys.exit(1)
    
    moderate_tiers = []
    for unit in units:
        try:
            tier = generate_moderate_tier(unit)
            moderate_tiers.append(tier)
        except Exception as e:
            logger.error(f"Error processing unit {unit.get('unit_id', 'unknown')}: {e}")
            # Fail loudly on data processing errors
            raise
    
    save_moderate_tiers(moderate_tiers, output_path)
    logger.info("Moderate tier generation completed successfully.")

if __name__ == "__main__":
    # Setup basic logging for script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()