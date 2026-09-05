import re
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("spec_update_t008b")

def update_spec_md():
    """
    Updates spec.md to replace 'bootstrap difference-of-means test (p ≤ 0.05)'
    with 'descriptive trend analysis' in SC-005, due to N=3 limitations.
    """
    spec_path = Path("projects/PROJ-424-investigating-the-predictive-power-of-mo/spec.md")
    
    if not spec_path.exists():
        logger.error(f"spec.md not found at {spec_path}")
        return False

    try:
        content = spec_path.read_text(encoding="utf-8")
        
        # Define the old and new text patterns
        old_text = r"bootstrap difference-of-means test \(p ≤ 0\.05\)"
        new_text = "descriptive trend analysis"
        
        # Perform the replacement
        new_content, count = re.subn(old_text, new_text, content)
        
        if count == 0:
            logger.warning("No occurrences of the target text found in spec.md. Checking if update is already applied.")
            # Check if the new text already exists to avoid false failure
            if "descriptive trend analysis" in content:
                logger.info("Spec already updated to 'descriptive trend analysis'.")
                return True
            else:
                logger.error("Target text not found and replacement not applied.")
                return False

        # Write the updated content back
        spec_path.write_text(new_content, encoding="utf-8")
        
        logger.info(f"Successfully updated SC-005 in spec.md. Replacements made: {count}")
        logger.info(f"Updated file: {spec_path}")
        
        return True

    except Exception as e:
        logger.error(f"Failed to update spec.md: {e}")
        return False

def main():
    success = update_spec_md()
    if not success:
        logger.error("Task T008b update failed.")
        exit(1)
    else:
        logger.info("Task T008b update completed successfully.")

if __name__ == "__main__":
    main()