import sys
import os
from pathlib import Path
from code.schemas import export_schema_definitions
from code.utils import get_contracts_path, setup_logger
import yaml

def main():
    """
    Generate the dataset schema YAML file at contracts/dataset.schema.yaml
    """
    logger = setup_logger(__name__)
    
    # Ensure contracts directory exists
    contracts_path = get_contracts_path()
    contracts_path.mkdir(parents=True, exist_ok=True)
    
    output_file = contracts_path / "dataset.schema.yaml"
    
    logger.info(f"Generating schema at: {output_file}")
    
    # Export schema definitions
    schema_dict = export_schema_definitions(output_file)
    
    logger.info(f"Schema successfully generated at: {output_file}")
    
    # Verify the file exists
    if not output_file.exists():
        logger.error("Failed to create schema file")
        sys.exit(1)
        
    # Print summary
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        logger.info(f"Schema content:\n{content}")

if __name__ == "__main__":
    main()
