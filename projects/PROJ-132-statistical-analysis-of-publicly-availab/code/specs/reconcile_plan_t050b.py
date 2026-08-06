"""
Implementation for T050b: Reconcile GP Requirement.

Updates plan.md to change the "mandatory a priori Gaussian Process (GP)"
requirement to a "conditional GP" based on Moran's I diagnostics,
aligning with spec.md FR-004.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def reconcile_plan(plan_path: str) -> bool:
    """
    Update plan.md to change the GP requirement from mandatory to conditional.

    Args:
        plan_path: Path to the plan.md file.

    Returns:
        True if the file was successfully updated, False otherwise.
    """
    plan_file = Path(plan_path)

    if not plan_file.exists():
        logger.error(f"Plan file not found: {plan_path}")
        return False

    try:
        content = plan_file.read_text(encoding='utf-8')
        original_content = content

        # Define the old and new text patterns
        old_text = "mandatory a priori Gaussian Process (GP)"
        new_text = "conditional (applied if Moran's I > 0.15) Gaussian Process (GP)"

        # Check if the old text exists
        if old_text not in content:
            logger.warning(f"Text '{old_text}' not found in {plan_path}. "
                         "The requirement might already be updated or phrased differently.")
            # Check for alternative phrasing that might need updating
            if "mandatory a priori" in content:
                logger.warning("Found 'mandatory a priori' but not the full phrase. "
                             "Manual review recommended.")
            return False

        # Perform the replacement
        content = content.replace(old_text, new_text)

        # Write the updated content back
        plan_file.write_text(content, encoding='utf-8')

        logger.info(f"Successfully updated GP requirement in {plan_path}")
        logger.info(f"Changed: '{old_text}' -> '{new_text}'")

        return True

    except Exception as e:
        logger.error(f"Error updating plan file: {e}")
        return False

def main():
    """Main entry point for the reconciliation script."""
    # Determine the project root (assuming script is in code/specs/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    plan_path = project_root / "plan.md"

    logger.info(f"Starting GP requirement reconciliation for project at {project_root}")
    logger.info(f"Target file: {plan_path}")

    success = reconcile_plan(str(plan_path))

    if success:
        logger.info("Reconciliation completed successfully.")
        sys.exit(0)
    else:
        logger.error("Reconciliation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()