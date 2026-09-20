"""
Task T036: Update spec.md FR-008 R² threshold.

This script updates the specification file to align the R² threshold
requirement with the study's precision goals as defined in the Plan
and Constitution Principle VI.

It changes the requirement from 0.99 to 0.95.
"""
import re
import sys
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_spec_md(spec_path: Path) -> bool:
    """
    Updates the spec.md file to change FR-008 R² threshold from 0.99 to 0.95.
    
    Args:
        spec_path: Path to the spec.md file.
        
    Returns:
        True if update was successful, False otherwise.
    """
    if not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        return False

    try:
        content = spec_path.read_text(encoding='utf-8')
        original_content = content
        
        # Pattern to find FR-008 and update the R² threshold
        # Looking for "R² threshold" or "R-squared threshold" with value 0.99
        # We need to be precise to avoid changing other numbers
        patterns_to_replace = [
            # Match R² threshold = 0.99
            (r'(FR-008.*?R[²²]?\s*(threshold|requirement).*?)[0-9.]+', 
             lambda m: m.group(1) + '0.95'),
            # Match specific context "R² threshold: 0.99"
            (r'(R[²²]?\s*threshold\s*:\s*)0\.99', 
             r'\g<1>0.95'),
            # Match "R² = 0.99" in requirement context
            (r'(requirement.*?R[²²]?\s*=\s*)0\.99',
             r'\g<1>0.95'),
         ]

        updated_content = content
        for pattern, replacement in patterns_to_replace:
            updated_content = re.sub(pattern, replacement, updated_content, flags=re.DOTALL | re.IGNORECASE)

        # Also handle direct "0.99" to "0.95" in FR-008 context if regex fails
        # This is a fallback for specific formatting
        if "0.99" in updated_content and "FR-008" in updated_content:
            # Find the section containing FR-008 and replace 0.99 with 0.95
            fr008_match = re.search(r'(FR-008.*?)(?(0.99)(0.99))', updated_content, re.DOTALL)
            if fr008_match:
                # Replace only within the matched section if possible, otherwise global replacement in that block
                # Simpler: just replace the first occurrence of 0.99 after FR-008
                start = fr008_match.start()
                end = fr008_match.end()
                section = updated_content[start:end]
                section = section.replace("0.99", "0.95", 1) # Replace only first 0.99 in this section
                updated_content = updated_content[:start] + section + updated_content[end:]

        if updated_content == original_content:
            logger.warning("No changes made. Pattern might not match existing text format.")
            # Let's try a more aggressive replacement for the specific known text if regex is tricky
            # Common format: "R² threshold = 0.99"
            if "R² threshold = 0.99" in content:
                content = content.replace("R² threshold = 0.99", "R² threshold = 0.95")
                updated_content = content
                logger.info("Applied direct string replacement for 'R² threshold = 0.99'.")
            elif "R-squared threshold = 0.99" in content:
                content = content.replace("R-squared threshold = 0.99", "R-squared threshold = 0.95")
                updated_content = content
                logger.info("Applied direct string replacement for 'R-squared threshold = 0.99'.")
            elif "R2 threshold = 0.99" in content:
                content = content.replace("R2 threshold = 0.99", "R2 threshold = 0.95")
                updated_content = content
                logger.info("Applied direct string replacement for 'R2 threshold = 0.99'.")
            else:
                logger.error("Could not identify the R² threshold pattern to update.")
                return False

        if updated_content != original_content:
            spec_path.write_text(updated_content, encoding='utf-8')
            logger.info(f"Successfully updated {spec_path} (FR-008 R² threshold changed to 0.95).")
            return True
        else:
            logger.error("Failed to update the file content.")
            return False

    except Exception as e:
        logger.error(f"Error updating spec file: {e}")
        return False

def main():
    """Main entry point for the script."""
    project_root = Path(__file__).parent.parent
    spec_path = project_root / "specs" / "001-investigating-md-diffusion-predictive-power" / "spec.md"
    
    logger.info(f"Targeting spec file: {spec_path}")
    
    if update_spec_md(spec_path):
        logger.info("Task T036 completed successfully.")
        return 0
    else:
        logger.error("Task T036 failed to update the spec file.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
