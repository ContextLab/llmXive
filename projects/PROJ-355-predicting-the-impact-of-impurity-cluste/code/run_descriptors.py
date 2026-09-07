"""
Runner script for descriptor computation.
This script executes the descriptor computation pipeline and saves results.
"""
import logging
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.descriptors import run_descriptor_computation
from code.config import get_project_root

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for running descriptor computation."""
    logger.info("Starting descriptor computation pipeline...")

    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "gb_supercells"
    output_path = project_root / "data" / "processed" / "descriptors.csv"

    try:
        # Check if input directory exists
        if not input_path.exists():
            logger.error(f"Input directory does not exist: {input_path}")
            logger.error("Please run gb_builder.py first to generate GB supercells.")
            sys.exit(1)

        # Run descriptor computation
        df = run_descriptor_computation(input_path, output_path)

        logger.info(f"Descriptor computation completed successfully.")
        logger.info(f"Output saved to: {output_path}")
        logger.info(f"Total configurations processed: {len(df)}")

        # Print summary
        if not df.empty:
            logger.info("Descriptor summary:")
            logger.info(df.describe())

    except Exception as e:
        logger.error(f"Descriptor computation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
