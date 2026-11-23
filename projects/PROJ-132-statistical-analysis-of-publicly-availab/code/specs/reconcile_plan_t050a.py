"""
Task T050a: Reconcile Tail-Sampling Requirement.

This script updates plan.md to remove any mention of "FR-002-S" or 
"Tail-Preserving Stratified Sampling", ensuring alignment with spec.md FR-002.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reconcile_plan(plan_path: Path) -> bool:
    """
    Update plan.md to remove mentions of FR-002-S or Tail-Preserving Stratified Sampling.
    
    Args:
        plan_path: Path to the plan.md file
        
    Returns:
        True if modifications were made or file was already clean, False on error
    """
    if not plan_path.exists():
        logger.error(f"Plan file not found: {plan_path}")
        return False
    
    try:
        content = plan_path.read_text(encoding='utf-8')
        original_content = content
        
        # Terms to remove
        terms_to_remove = [
            "FR-002-S",
            "Tail-Preserving Stratified Sampling",
            "tail-preserving stratified sampling",
            "tail preserving stratified sampling"
        ]
        
        modifications_made = False
        
        for term in terms_to_remove:
            if term in content:
                logger.info(f"Removing term: '{term}'")
                content = content.replace(term, "")
                modifications_made = True
        
        # Clean up any double spaces or newlines created by removals
        content = content.replace("  ", " ").replace("\n\n\n", "\n\n")
        
        if modifications_made:
            plan_path.write_text(content, encoding='utf-8')
            logger.info(f"Successfully updated {plan_path}")
            return True
        else:
            logger.info(f"No modifications needed for {plan_path} - terms not found")
            return True
            
    except Exception as e:
        logger.error(f"Error updating plan file: {e}")
        return False

def main():
    """Main entry point for T050a reconciliation."""
    # Determine project root
    project_root = Path(__file__).parent.parent.parent
    plan_path = project_root / "plan.md"
    
    logger.info(f"Starting T050a reconciliation for plan at: {plan_path}")
    
    success = reconcile_plan(plan_path)
    
    if success:
        logger.info("T050a reconciliation completed successfully")
        sys.exit(0)
    else:
        logger.error("T050a reconciliation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
