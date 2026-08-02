"""
Runner script to execute model generation for specific contracts.
"""
import os
import sys
import logging
from pathlib import Path
from scripts.generate_models import load_schema, get_field_type, generate_model_class, verify_generation, main as generate_main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main_execution():
    """
    Executes the generation for T008b (FeatureVector).
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Project root relative to this script (assuming code/scripts/)
    project_root = Path(__file__).parent.parent
    contracts_dir = project_root / "contracts"
    models_dir = project_root / "src" / "models"
    
    schema_file = contracts_dir / "feature.schema.yaml"
    output_file = models_dir / "feature_vector.py"
    class_name = "FeatureVector"
    
    logger.info(f"Starting generation for {class_name}...")
    logger.info(f"Schema: {schema_file}")
    logger.info(f"Output: {output_file}")
    
    if not schema_file.exists():
        logger.error(f"Schema file missing: {schema_file}")
        sys.exit(1)
    
    # Run generation
    try:
        exit_code = generate_main(str(schema_file), str(output_file), class_name)
        if exit_code == 0:
            logger.info("Model generation successful.")
            return 0
        else:
            logger.error("Model generation failed verification.")
            return 1
    except Exception as e:
        logger.error(f"Unexpected error during generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_execution())