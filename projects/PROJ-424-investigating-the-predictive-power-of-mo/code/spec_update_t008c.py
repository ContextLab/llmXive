import re
from pathlib import Path
from datetime import datetime
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_spec_md(spec_path: Path) -> None:
    """
    Updates spec.md to define sensitivity sweep parameters in SC-003.
    
    Replaces the '[deferred]' placeholders in SC-003 with concrete values:
    {low, medium, high percentages} corresponding to 10%, 20%, and 30% 
    of the total trajectory length, as defined in Plan and US-2.
    """
    if not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    original_content = spec_path.read_text(encoding='utf-8')
    new_content = original_content

    # Pattern to match SC-003 block or the specific line containing the deferred values
    # We look for the specific phrase in SC-003 regarding sensitivity sweep parameters
    old_pattern = r"Sensitivity sweep parameters as \{low, medium, high percentages\} \(removing \[deferred\] status\)"
    
    # If the text is already updated, we might not need to do anything, 
    # but we check for the specific placeholder text usually found in the task description
    # or the actual spec content that needs updating.
    # Based on the task: "Update `spec.md` SC-003 to define sensitivity sweep parameters..."
    # We assume the spec.md currently contains a placeholder or the task description text 
    # that needs to be replaced with the concrete definition.
    
    # Let's look for a common placeholder pattern in specs for deferred items
    # or the specific text from the task if it was pasted into the spec as a TODO.
    # A safer regex for the specific content change described:
    # Replace "sensitivity sweep parameters as {[deferred], [deferred], [deferred]}" 
    # with concrete values.
    
    # Attempt 1: Replace the specific placeholder pattern often used in generated specs
    placeholder_pattern = r"sensitivity sweep parameters as \[deferred\], \[deferred\], and \[deferred\]"
    replacement_text = "sensitivity sweep parameters as {low (10%), medium (20%), and high (30%) percentages of total trajectory length}"
    
    if re.search(placeholder_pattern, new_content, re.IGNORECASE):
        new_content = re.sub(
            placeholder_pattern, 
            replacement_text, 
            new_content, 
            flags=re.IGNORECASE
        )
        logger.info("Updated SC-003: Replaced [deferred] placeholders with concrete percentages.")
    else:
        # Attempt 2: Check if the text is already updated or if the pattern is slightly different
        # Look for "sensitivity sweep parameters" and ensure it doesn't contain "[deferred]"
        if "sensitivity sweep parameters" in new_content:
            if "[deferred]" in new_content:
                # Fallback: replace any occurrence of [deferred] in the context of sensitivity
                # This is a bit risky but handles the case if the pattern is loose
                new_content = re.sub(
                    r"\[deferred\]", 
                    "10%, 20%, and 30%", 
                    new_content, 
                    count=3 # Limit to 3 replacements to avoid over-correcting
                )
                logger.info("Updated SC-003: Replaced [deferred] with 10%, 20%, 30% (fallback method).")
            else:
                logger.info("SC-003 appears to already be updated or does not contain [deferred].")
        else:
            logger.warning("Could not locate SC-003 sensitivity sweep parameters section to update.")

    if new_content != original_content:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_note = f"\n# Updated by T008c at {timestamp}: Defined sensitivity sweep parameters (10%, 20%, 30%).\n"
        # Insert note at the top or just overwrite
        spec_path.write_text(new_content, encoding='utf-8')
        logger.info(f"Successfully updated {spec_path}")
    else:
        logger.info("No changes were made to spec.md (content matches expected state).")

def main():
    project_root = Path(__file__).parent.parent
    spec_path = project_root / "spec.md"
    
    logger.info(f"Starting T008c spec update for {spec_path}")
    try:
        update_spec_md(spec_path)
    except Exception as e:
        logger.error(f"Failed to update spec.md: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()