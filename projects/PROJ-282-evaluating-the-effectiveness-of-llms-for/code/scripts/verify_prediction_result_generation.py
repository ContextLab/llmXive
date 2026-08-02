"""
Verification script for T009b: Generate and verify PredictionResult model.

This script:
1. Verifies that contracts/prediction.schema.yaml exists
2. Generates src/models/prediction_result.py from the schema
3. Verifies the generated model matches the schema
"""
import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.generate_models import load_schema, get_field_type, generate_model_class, verify_generation
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main execution for T009b verification."""
    logger.info("Starting T009b: Generate PredictionResult model from contract")

    # Paths
    schema_path = project_root / "contracts" / "prediction.schema.yaml"
    output_path = project_root / "src" / "models" / "prediction_result.py"

    # Pre-check: Verify T009a (schema) exists
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        logger.error("T009a must complete before T009b can run.")
        return False

    logger.info(f"Schema file found: {schema_path}")

    # Load schema
    try:
        schema = load_schema(schema_path)
        logger.info(f"Schema loaded successfully: {schema}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    # Verify schema structure
    required_keys = ["type", "properties", "required"]
    for key in required_keys:
        if key not in schema:
            logger.error(f"Schema missing required key: {key}")
            return False

    expected_fields = ["snippet_id", "predicted_label", "predicted_category", "is_correct", "inference_time_ms"]
    for field in expected_fields:
        if field not in schema.get("properties", {}):
            logger.error(f"Schema missing expected field: {field}")
            return False

    logger.info("Schema structure validated")

    # Generate model
    try:
        generated_code = generate_model_class(
            schema=schema,
            class_name="PredictionResult",
            schema_class_name="PredictionResultSchema"
        )
        logger.info("Model generation successful")
    except Exception as e:
        logger.error(f"Model generation failed: {e}")
        return False

    # Write generated code
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(generated_code)
        logger.info(f"Generated model written to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write generated model: {e}")
        return False

    # Verify generation
    try:
        success = verify_generation(
            schema=schema,
            output_path=output_path,
            expected_class_names=["PredictionResult", "PredictionResultSchema"]
        )
        
        if success:
            logger.info("Generation verification PASSED")
            logger.info("T009b completed successfully")
            return True
        else:
            logger.error("Generation verification FAILED")
            return False
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)