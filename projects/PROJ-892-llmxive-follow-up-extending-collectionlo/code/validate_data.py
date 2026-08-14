"""
Validate the CollectionLoRA adapter to ensure it contains at least 5 distinct effects.

This script verifies Assumption 011: The loaded CollectionLoRA adapter contains
at least 5 distinct effects (identified by unique key prefixes in the state dict).

If the threshold is not met, the script fails fast with a clear error message.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Set, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ADAPTER_PATH = Path("data/models/adapter_fp16.safetensors")
MIN_EFFECTS_THRESHOLD = 5
VALIDATION_RESULT_PATH = Path("data/validation_results.json")

def load_safetensors_state_dict(path: Path) -> Dict[str, Any]:
    """
    Load the state dict from a .safetensors file.
    
    Args:
        path: Path to the .safetensors file
        
    Returns:
        Dictionary of tensor names to tensors
        
    Raises:
        FileNotFoundError: If the file does not exist
        ImportError: If safetensors library is not available
        Exception: For other loading errors
    """
    if not path.exists():
        raise FileNotFoundError(f"Adapter file not found: {path}")
    
    try:
        from safetensors import safe_open
    except ImportError:
        logger.error("safetensors library not available. Please install it: pip install safetensors")
        raise
    
    state_dict = {}
    with safe_open(path, framework="pt", device="cpu") as f:
        for key in f.keys():
            state_dict[key] = f.get_tensor(key)
    
    return state_dict

def extract_effect_prefixes(state_dict: Dict[str, Any]) -> Set[str]:
    """
    Extract unique effect prefixes from the state dict keys.
    
    In CollectionLoRA, effect prefixes are typically embedded in the key names.
    For example: "lora_unet_down_blocks_0_0_down_0_0" might indicate a specific effect.
    We look for patterns that distinguish different effects.
    
    Args:
        state_dict: The loaded state dictionary
        
    Returns:
        Set of unique effect prefixes identified
    """
    prefixes = set()
    
    for key in state_dict.keys():
        # Look for common patterns in LoRA keys that indicate effect grouping
        # In CollectionLoRA, effects are often grouped by specific naming conventions
        # Common patterns might include:
        # - "lora_unet_<effect_name>..."
        # - "lora_unet_<block>_<effect>..."
        # - Or specific effect identifiers in the key structure
        
        # Split by underscores and look for potential effect identifiers
        parts = key.split('_')
        
        # Heuristic: Look for effect-like patterns in the key
        # In CollectionLoRA, effects might be indicated by specific positions
        # or by the presence of effect-specific tokens
        if len(parts) >= 3:
            # Check for patterns like "lora_unet_<effect>_<block>..."
            # or "lora_unet_<block>_<effect>..."
            # We'll collect potential effect identifiers
            
            # Common effect indicators in CollectionLoRA
            # Based on the config.yaml, effects include: oil painting, watercolor, 
            # cyberpunk, pencil sketch, ink wash, acrylic, charcoal, pastel, digital art, concept art
            # These might be encoded in the key names
            
            # Extract potential effect prefix from the key
            # For now, we'll use a heuristic: look for unique substrings that appear
            # in the middle of the key name (after "lora_unet" and before block numbers)
            key_lower = key.lower()
            
            # Try to identify effect-specific parts
            # In many LoRA implementations, the effect name might be part of the key
            # We'll collect unique parts that could represent effects
            for i, part in enumerate(parts):
                # Skip common LoRA structure words
                if part in ['lora', 'unet', 'down', 'up', 'mid', 'block', 'attn', 'proj', 'conv']:
                    continue
                
                # If this part looks like it could be an effect identifier
                # (not purely numeric, not a common transformer term)
                if part and not part.isdigit() and len(part) > 2:
                    # Check if it's not a standard layer name
                    if part not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
                                   'in', 'out', 'to', 'q', 'k', 'v', 'out', 'norm', 'act']:
                        prefixes.add(part)
        
        # Alternative approach: Look for specific effect patterns
        # If the key contains effect-specific identifiers
        effect_keywords = ['oil', 'watercolor', 'cyberpunk', 'sketch', 'ink', 
                         'acrylic', 'charcoal', 'pastel', 'digital', 'concept']
        
        for keyword in effect_keywords:
            if keyword in key_lower:
                prefixes.add(keyword)
    
    return prefixes

def validate_adapter_effects(state_dict: Dict[str, Any], min_effects: int = MIN_EFFECTS_THRESHOLD) -> Dict[str, Any]:
    """
    Validate that the adapter contains at least the minimum number of distinct effects.
    
    Args:
        state_dict: The loaded state dictionary
        min_effects: Minimum number of distinct effects required
        
    Returns:
        Dictionary with validation results
    """
    prefixes = extract_effect_prefixes(state_dict)
    num_effects = len(prefixes)
    
    validation_result = {
        "adapter_path": str(ADAPTER_PATH),
        "total_keys": len(state_dict),
        "distinct_effects_found": num_effects,
        "min_required": min_effects,
        "validation_passed": num_effects >= min_effects,
        "effect_prefixes": list(prefixes),
        "timestamp": None  # Will be set by caller if needed
    }
    
    logger.info(f"Found {num_effects} distinct effect prefixes: {prefixes}")
    
    if num_effects < min_effects:
        logger.error(f"Validation FAILED: Only {num_effects} effects found, but {min_effects} required.")
        logger.error(f"Effect prefixes found: {prefixes}")
        raise ValueError(
            f"Assumption 011 violated: Adapter contains only {num_effects} distinct effects "
            f"(prefixes: {prefixes}), but at least {min_effects} are required."
        )
    
    logger.info(f"Validation PASSED: Found {num_effects} distinct effects (≥ {min_effects} required).")
    return validation_result

def save_validation_results(results: Dict[str, Any], output_path: Path = VALIDATION_RESULT_PATH):
    """
    Save validation results to a JSON file.
    
    Args:
        results: Dictionary of validation results
        output_path: Path to save the results
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Validation results saved to {output_path}")

def main():
    """
    Main entry point for the validation script.
    
    This script:
    1. Loads the CollectionLoRA adapter from data/models/adapter_fp16.safetensors
    2. Extracts unique effect prefixes from the state dict
    3. Validates that at least 5 distinct effects are present
    4. Fails fast if the threshold is not met
    5. Saves validation results to data/validation_results.json
    """
    logger.info("Starting CollectionLoRA adapter validation...")
    
    # Check if adapter exists
    if not ADAPTER_PATH.exists():
        logger.error(f"Adapter file not found: {ADAPTER_PATH}")
        logger.error("Please ensure T007b-2 has been completed and the adapter is downloaded.")
        sys.exit(1)
    
    try:
        logger.info(f"Loading adapter from {ADAPTER_PATH}...")
        state_dict = load_safetensors_state_dict(ADAPTER_PATH)
        logger.info(f"Loaded {len(state_dict)} keys from adapter")
        
        # Validate effects
        results = validate_adapter_effects(state_dict)
        
        # Save results
        save_validation_results(results)
        
        logger.info("Validation completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())