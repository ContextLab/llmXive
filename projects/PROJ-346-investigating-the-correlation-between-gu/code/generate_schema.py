"""
Script to generate and export schema definitions to contracts/dataset.schema.yaml.
This script must be run before T011 to ensure schema validation is available.
"""
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from schemas import export_schema_definitions
from utils import get_contracts_path, setup_logger

logger = setup_logger(__name__)

def main():
    """Main entry point for schema generation."""
    logger.info("Starting schema generation for dataset validation...")
    
    try:
        # Ensure contracts directory exists
        contracts_dir = get_contracts_path()
        contracts_dir.mkdir(parents=True, exist_ok=True)
        
        # Export schema definitions
        output_path = export_schema_definitions()
        
        if os.path.exists(output_path):
            logger.info(f"SUCCESS: Schema file created at {output_path}")
            return 0
        else:
            logger.error("FAILED: Schema file was not created")
            return 1
            
    except Exception as e:
        logger.error(f"FAILED: Error generating schema: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())