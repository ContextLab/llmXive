"""
Script to add logging for excluded perturbations to the main pipeline.

This script modifies code/data/generate_perturbations.py to include
detailed logging of excluded perturbations (raw scores and reasons)
to data/logs/perturbation_raw.log.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_perturbation_logger, init_logging
from config import ensure_directories


def add_logging_to_generate_perturbations():
    """
    Add logging for excluded perturbations to generate_perturbations.py.
    
    This function reads the existing generate_perturbations.py file,
    adds the necessary logging code for excluded perturbations,
    and writes the updated content back to the file.
    """
    perturbations_file = project_root / "code" / "data" / "generate_perturbations.py"
    
    if not perturbations_file.exists():
        print(f"Error: {perturbations_file} does not exist.")
        return False
    
    # Read the existing content
    with open(perturbations_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if logging is already added
    if "log_excluded_perturbation" in content:
        print("Logging for excluded perturbations is already present.")
        return True
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize logging
    init_logging()
    logger = get_perturbation_logger()
    
    # Define the logging code to add
    logging_import = "from utils.logging import log_excluded_perturbation\n"
    
    # Find the imports section and add our import
    if logging_import not in content:
        # Add import after other imports
        lines = content.split('\n')
        import_end_idx = -1
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('from ') and not line.strip().startswith('import '):
                import_end_idx = i
                break
        
        if import_end_idx > 0:
            lines.insert(import_end_idx, logging_import.strip())
            content = '\n'.join(lines)
    
    # Find the function where filtering happens and add logging
    # Look for the pattern where perturbations are filtered
    logging_code = '''
def log_excluded_perturbation(perturbation_type, original_prompt, perturbed_prompt, raw_score, reason):
    """
    Log excluded perturbations with their raw scores and reasons.
    
    Args:
  perturbation_type (str): Type of perturbation (synonym, typo, rephrase)
  original_prompt (str): Original prompt text
  perturbed_prompt (str): Perturbed prompt text
  raw_score (float): Raw semantic similarity score
  reason (str): Reason for exclusion (e.g., score below threshold)
    """
    logger = get_perturbation_logger()
    logger.info(f"EXCLUDED: type={perturbation_type}, score={raw_score:.4f}, reason={reason}")
    logger.debug(f"Original: {original_prompt[:100]}...")
    logger.debug(f"Perturbed: {perturbed_prompt[:100]}...")
'''
    
    # Add the logging function before the main logic
    if "def log_excluded_perturbation" not in content:
        # Find a good place to insert the function (after imports, before main functions)
        lines = content.split('\n')
        insert_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('def ') and i > 5:  # Skip early definitions
                insert_idx = i
                break
        
        if insert_idx > 0:
            lines.insert(insert_idx, logging_code)
            content = '\n'.join(lines)
    
    # Now find where filtering happens and add logging calls
    # Look for patterns like "if score < threshold" or "if not valid"
    # We need to add logging before these exclusions
    
    # Pattern 1: After semantic validation, before filtering
    if "validate_perturbation" in content and "if score" in content:
        # Add logging call after validation
        lines = content.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            # Check if this is a validation call followed by a score check
            if "validate_perturbation" in line and "score" in lines[i+1] if i+1 < len(lines) else False:
                # Add logging for excluded cases
                new_lines.append("                    log_excluded_perturbation(perturbation_type, original_prompt, perturbed_prompt, score, 'score_below_threshold')")
        
        content = '\n'.join(new_lines)
    
    # Write the updated content back
    with open(perturbations_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully added logging for excluded perturbations to {perturbations_file}")
    return True


if __name__ == "__main__":
    success = add_logging_to_generate_perturbations()
    if not success:
        sys.exit(1)