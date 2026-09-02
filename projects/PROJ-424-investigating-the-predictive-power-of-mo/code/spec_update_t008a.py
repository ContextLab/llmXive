"""
Task T008a: Spec Kickback - Update FR-008 MSD Linearity Threshold.

Updates spec.md to change the MSD linearity threshold from R² >= 0.99
to R² >= 0.95, aligning with Constitution Principle VI.

This script modifies the spec.md file in the project root.
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
    Update the spec.md file to change FR-008 threshold from 0.99 to 0.95.

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
        
        # Pattern to find FR-008 with the old threshold (0.99)
        # We look for the specific requirement text and update the value
        old_pattern = r'(FR-008.*?R²\s*≥\s*)0\.99'
        new_value = '0.95'
        
        # Check if the pattern exists
        if not re.search(old_pattern, content, re.IGNORECASE | re.DOTALL):
            logger.warning("FR-008 with R² >= 0.99 pattern not found. Checking for alternative formats...")
            # Try a more flexible pattern
            alt_pattern = r'(FR-008.*?threshold.*?R²\s*≥\s*)0\.99'
            if re.search(alt_pattern, content, re.IGNORECASE | re.DOTALL):
                content = re.sub(alt_pattern, rf'\g<1>{new_value}', content, flags=re.IGNORECASE | re.DOTALL)
            else:
                # Try finding FR-008 and updating any R² >= 0.99 in its vicinity
                # This is a fallback strategy
                lines = content.split('\n')
                updated = False
                in_fr008 = False
                
                for i, line in enumerate(lines):
                    if 'FR-008' in line:
                        in_fr008 = True
                    if in_fr008 and 'R²' in line and '0.99' in line:
                        lines[i] = line.replace('0.99', '0.95')
                        logger.info(f"Updated line {i+1}: {lines[i].strip()}")
                        updated = True
                        # Reset flag after finding the relevant line
                        in_fr008 = False
                
                if updated:
                    content = '\n'.join(lines)
                else:
                    logger.error("Could not locate FR-008 R² threshold in spec.md.")
                    return False
        else:
            content = re.sub(old_pattern, rf'\g<1>{new_value}', content, flags=re.IGNORECASE | re.DOTALL)
            logger.info("Updated FR-008 R² threshold from 0.99 to 0.95 using primary pattern.")

        if content == original_content:
            logger.warning("No changes were made to spec.md. Pattern might have already been updated or format differs.")
            # Check if it's already 0.95
            if '0.95' in content and 'FR-008' in content:
                logger.info("FR-008 appears to already reference 0.95.")
                return True
            return False

        # Add a comment/note about the update for audit trail
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note = f"\n<!-- Updated by T008a on {timestamp}: Aligned FR-008 with Constitution Principle VI (R² >= 0.95) -->\n"
        
        # Insert note near the top of the file or after the first header
        if content.startswith('#'):
            lines = content.split('\n', 1)
            if len(lines) > 1:
                content = lines[0] + note + lines[1]
            else:
                content += note
        
        spec_path.write_text(content, encoding='utf-8')
        logger.info(f"Successfully updated {spec_path}")
        return True

    except Exception as e:
        logger.error(f"Error updating spec.md: {e}")
        return False

def main():
    """Main entry point for the script."""
    # Determine project root (assuming script is in code/ subdirectory)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    spec_path = project_root / "spec.md"

    logger.info(f"Looking for spec.md at: {spec_path}")

    if update_spec_md(spec_path):
        logger.info("T008a execution completed successfully.")
        return 0
    else:
        logger.error("T008a execution failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
