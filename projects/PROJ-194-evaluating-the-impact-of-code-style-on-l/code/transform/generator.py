import os
import json
import ast
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

from transform.formatters.black_formatter import apply_black_format
from transform.formatters.minified_formatter import apply_minified_format
from transform.renamer.ast_renamer import apply_generic_naming
from transform.stripper.comment_stripper import strip_comments_and_docstrings
from transform.seed_manager import log_transform_seed, compute_mapping_hash
from transform.validator import validate_python_syntax, ValidationError

# Configuration for the 2x2x2 factorial design
FACTORIAL_CONFIG = {
    "formatting": ["black", "minified"],
    "naming": ["original", "generic"],
    "comments": ["present", "stripped"]
}

def _compute_variant_flags(formatting: str, naming: str, comments: str) -> Dict[str, bool]:
    """
    Compute boolean flags for a specific variant configuration.
    
    Args:
        formatting: 'black' or 'minified'
        naming: 'original' or 'generic'
        comments: 'present' or 'stripped'
        
    Returns:
        Dictionary with boolean flags for metadata.
    """
    is_generic_naming = (naming == "generic")
    is_stripped_comments = (comments == "stripped")
    is_minified = (formatting == "minified")
    
    # Semantic Opacity: True if generic naming AND stripped comments
    is_semantic_opacity = is_generic_naming and is_stripped_comments
    
    return {
        "is_generic_naming": is_generic_naming,
        "is_stripped_comments": is_stripped_comments,
        "is_minified": is_minified,
        "is_semantic_opacity": is_semantic_opacity
    }

def _generate_variant(
    base_code: str,
    base_id: str,
    formatting: str,
    naming: str,
    comments: str,
    seed: int
) -> Optional[Dict[str, Any]]:
    """
    Generate a single code variant based on the factorial configuration.
    
    Args:
        base_code: Original Python code string.
        base_id: Unique identifier for the base function.
        formatting: Formatting style ('black' or 'minified').
        naming: Naming style ('original' or 'generic').
        comments: Comment style ('present' or 'stripped').
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing the variant code, metadata, and flags, or None if invalid.
    """
    current_code = base_code
    transformation_log = []
    
    # 1. Apply Formatting
    if formatting == "black":
        try:
            current_code = apply_black_format(current_code)
            transformation_log.append("black_format")
        except Exception as e:
            # If Black fails (e.g., syntax error in base), we might skip or fallback
            # For now, we assume base is valid per T008, but Black might fail on edge cases
            return None
    elif formatting == "minified":
        try:
            current_code = apply_minified_format(current_code)
            transformation_log.append("minified_format")
        except Exception as e:
            return None
    
    # 2. Apply Naming
    if naming == "generic":
        try:
            # apply_generic_naming returns (new_code, mapping_dict)
            new_code, mapping_dict = apply_generic_naming(current_code, seed=seed)
            current_code = new_code
            transformation_log.append("generic_naming")
            # Compute hash of mapping for reproducibility
            mapping_hash = compute_mapping_hash(mapping_dict)
        except Exception as e:
            return None
    else:
        mapping_dict = {}
        mapping_hash = None
    
    # 3. Apply Comment Stripping
    if comments == "stripped":
        try:
            # strip_comments_and_docstrings returns (new_code, original_docstring)
            new_code, original_docstring = strip_comments_and_docstrings(current_code)
            current_code = new_code
            transformation_log.append("stripped_comments")
        except Exception as e:
            return None
    else:
        original_docstring = None
    
    # Validate the final code
    if not validate_python_syntax(current_code):
        return None
    
    # Compute flags
    flags = _compute_variant_flags(formatting, naming, comments)
    
    # Log seed info
    seed_entry = {
        "base_id": base_id,
        "transform_seed": seed,
        "mapping_hash": mapping_hash,
        "config": {
            "formatting": formatting,
            "naming": naming,
            "comments": comments
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    log_transform_seed(seed_entry)
    
    return {
        "base_id": base_id,
        "variant_id": f"{base_id}_{formatting}_{naming}_{comments}",
        "code": current_code,
        "metadata": {
            "formatting": formatting,
            "naming": naming,
            "comments": comments,
            "seed": seed,
            "transformation_log": transformation_log,
            "original_docstring": original_docstring
        },
        "flags": flags
    }

def generate_all_variants(
    base_functions: List[Dict[str, Any]],
    output_dir: str = "data/derived"
) -> List[Dict[str, Any]]:
    """
    Generate all 8 style variants for a list of base functions.
    
    Args:
        base_functions: List of dicts with 'id' and 'code'.
        output_dir: Directory to save the results.
        
    Returns:
        List of all generated variant dictionaries.
    """
    all_variants = []
    
    os.makedirs(output_dir, exist_ok=True)
    
    for func in base_functions:
        base_id = func["id"]
        base_code = func["code"]
        
        # Use a deterministic seed based on base_id and a base salt
        # In a real pipeline, this seed would be managed centrally
        base_salt = 12345 
        seed = int(hashlib.md5(f"{base_id}_{base_salt}".encode()).hexdigest(), 16) % (2**32)
        
        for formatting in FACTORIAL_CONFIG["formatting"]:
            for naming in FACTORIAL_CONFIG["naming"]:
                for comments in FACTORIAL_CONFIG["comments"]:
                    # Increment seed for each variant to ensure diversity in renamer if needed
                    current_seed = seed + len(all_variants)
                    
                    variant = _generate_variant(
                        base_code=base_code,
                        base_id=base_id,
                        formatting=formatting,
                        naming=naming,
                        comments=comments,
                        seed=current_seed
                    )
                    
                    if variant:
                        all_variants.append(variant)
    
    # Save the aggregated results
    output_path = os.path.join(output_dir, "variants.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_variants, f, indent=2)
        
    return all_variants

def main():
    """
    CLI entry point for generating variants.
    Expects a JSON file of base functions as input.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m code.transform.generator <input_json_path>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
        
    with open(input_path, "r", encoding="utf-8") as f:
        base_functions = json.load(f)
        
    print(f"Generating variants for {len(base_functions)} base functions...")
    variants = generate_all_variants(base_functions)
    print(f"Successfully generated {len(variants)} variants.")

if __name__ == "__main__":
    main()