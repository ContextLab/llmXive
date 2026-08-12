import os
import sys
import argparse
from pathlib import Path
from typing import Optional
from utils.logging import get_logger

logger = get_logger(__name__)

def apply_patch(plan_path: Path, patch_path: Path) -> bool:
    """
    Applies the generated patch to the plan.md file.
    
    This function reads the patch file created by T003b and applies it to plan.md.
    It uses a simple string replacement approach since we control the patch format.
    
    Args:
        plan_path: Path to the plan.md file to be patched
        patch_path: Path to the patch file containing the corrections
        
    Returns:
        bool: True if patch was applied successfully, False otherwise
    """
    logger.info(f"Applying patch from {patch_path} to {plan_path}")
    
    if not plan_path.exists():
        logger.error(f"Plan file not found: {plan_path}")
        return False
        
    if not patch_path.exists():
        logger.error(f"Patch file not found: {patch_path}")
        return False
        
    try:
        # Read the original plan
        with open(plan_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Read the patch
        with open(patch_path, 'r', encoding='utf-8') as f:
            patch_content = f.read()
        
        # Parse the patch to extract replacements
        # Format: OLD_TEXT -> NEW_TEXT
        replacements = {}
        for line in patch_content.strip().split('\n'):
            if ' -> ' in line:
                old_text, new_text = line.split(' -> ', 1)
                replacements[old_text] = new_text
        
        # Apply replacements
        modified_content = original_content
        changes_made = False
        
        for old_text, new_text in replacements.items():
            if old_text in modified_content:
                modified_content = modified_content.replace(old_text, new_text)
                changes_made = True
                logger.info(f"Replaced: '{old_text[:50]}...' -> '{new_text[:50]}...'")
            else:
                logger.warning(f"Text not found for replacement: '{old_text[:50]}...'")
        
        if not changes_made:
            logger.warning("No changes were made to the plan file")
            return False
        
        # Write the modified content back
        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        logger.info(f"Successfully applied patch to {plan_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error applying patch: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

def main():
    """Main entry point for the plan applier script."""
    parser = argparse.ArgumentParser(description='Apply patch to plan.md')
    parser.add_argument('--plan-path', type=str, default='projects/PROJ-558-consciousness-bootstrapping-self-aware-a/plan.md',
                      help='Path to the plan.md file')
    parser.add_argument('--patch-path', type=str, default='projects/PROJ-558-consciousness-bootstrapping-self-aware-a/patches/plan_correction.patch',
                      help='Path to the patch file')
    
    args = parser.parse_args()
    
    plan_path = Path(args.plan_path)
    patch_path = Path(args.patch_path)
    
    success = apply_patch(plan_path, patch_path)
    
    if success:
        logger.info("Plan correction applied successfully")
        sys.exit(0)
    else:
        logger.error("Failed to apply plan correction")
        sys.exit(1)

if __name__ == '__main__':
    main()