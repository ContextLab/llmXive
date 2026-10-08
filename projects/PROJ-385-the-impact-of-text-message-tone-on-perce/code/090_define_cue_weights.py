"""
T090: Cue-Intensity Weighting Schemes.

Generates and saves three weighting schemes for cue intensity calculation:
1. Equal: Equal distribution across emoji, punctuation, and length.
2. Emoji-Dominant: Majority weight on emoji, minority on others.
3. Punctuation-Dominant: High weight on punctuation, low on others.

All weights are normalized to sum to unity (1.0) and rounded to 10 decimal places.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import get_processed_data_dir
from logging_config import setup_logging, get_logger

# Initialize logger
setup_logging()
logger = get_logger(__name__)

def round_normalized_weights(weights: Tuple[float, float, float]) -> Dict[str, float]:
    """
    Round weights to 10 decimal places and assign remainder to the last component
    to ensure they sum exactly to 1.0.
    
    Args:
        weights: Tuple of (emoji, punctuation, length) weights.
        
    Returns:
        Dictionary with rounded weights ensuring sum is exactly 1.0.
    """
    # Round to 10 decimal places
    rounded = [round(w, 10) for w in weights]
    
    # Calculate sum and remainder
    current_sum = sum(rounded)
    remainder = 1.0 - current_sum
    
    # Assign remainder to the last component (length)
    rounded[-1] += remainder
    
    # Ensure no floating point drift issues by final rounding
    rounded[-1] = round(rounded[-1], 10)
    
    return {
        "emoji": rounded[0],
        "punctuation": rounded[1],
        "length": rounded[2]
    }

def get_cue_intensity_schemes() -> List[Dict[str, Any]]:
    """
    Generate the three cue intensity weighting schemes.
    
    Returns:
        List of dictionaries, each containing a scheme name and its weights.
        Tuple order is always (emoji, punctuation, length).
    """
    schemes = []
    
    # 1. Equal Distribution
    # Each component gets approximately 1/3
    equal_weights = (1/3, 1/3, 1/3)
    schemes.append({
        "name": "equal",
        "description": "Equal distribution across all cues",
        "theoretical_basis": "No prior assumption about cue dominance; treats all cues as equally informative.",
        "weights": round_normalized_weights(equal_weights)
    })
    
    # 2. Emoji-Dominant
    # Theory: Emoji use is the primary driver of perceived warmth.
    # Assign 0.7 to emoji, 0.15 to punctuation, 0.15 to length
    emoji_dominant_weights = (0.7, 0.15, 0.15)
    schemes.append({
        "name": "emoji_dominant",
        "description": "Emoji use is the primary driver of perceived warmth",
        "theoretical_basis": "Emoji use is the primary driver of perceived warmth.",
        "weights": round_normalized_weights(emoji_dominant_weights)
    })
    
    # 3. Punctuation-Dominant
    # Theory: Punctuation intensity signals emotional arousal.
    # Assign 0.15 to emoji, 0.7 to punctuation, 0.15 to length
    punctuation_dominant_weights = (0.15, 0.7, 0.15)
    schemes.append({
        "name": "punctuation_dominant",
        "description": "Punctuation intensity signals emotional arousal",
        "theoretical_basis": "Punctuation intensity signals emotional arousal.",
        "weights": round_normalized_weights(punctuation_dominant_weights)
    })
    
    return schemes

def save_schemes(schemes: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the weighting schemes to a JSON file.
    
    Args:
        schemes: List of scheme dictionaries.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schemes, f, indent=2)
    
    logger.info(f"Saved cue intensity schemes to {output_path}")

def main() -> int:
    """
    Main entry point for T090.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Get output path
        processed_dir = get_processed_data_dir()
        output_path = processed_dir / "cue_intensity_weights.json"
        
        # Generate schemes
        schemes = get_cue_intensity_schemes()
        
        # Save to file
        save_schemes(schemes, output_path)
        
        # Verify the output
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        # Validate that each scheme's weights sum to 1.0
        for scheme in loaded:
            weights = scheme['weights']
            total = weights['emoji'] + weights['punctuation'] + weights['length']
            if not abs(total - 1.0) < 1e-9:
                logger.error(f"Scheme {scheme['name']} weights sum to {total}, not 1.0")
                return 1
            
            logger.info(f"Scheme '{scheme['name']}': {scheme['weights']} (sum={total})")
        
        logger.info("T090 completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Error in T090: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
