"""
Script to execute the schema-to-code generation for AnalysisMetric.
This task (T009e) runs after T009d (schema creation) and verifies the output.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.generate_models import load_schema, get_field_type, generate_model_class, verify_generation
from src.utils.logger import get_logger

def main():
    logger = get_logger("T009e_AnalysisMetricGenerator")
    logger.info("Starting AnalysisMetric schema generation (T009e)")

    schema_path = project_root / "contracts" / "analysis_metric.schema.yaml"
    output_path = project_root / "src" / "models" / "analysis_metric.py"

    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        logger.error("Prerequisite T009d (schema creation) may not be complete.")
        sys.exit(1)

    logger.info(f"Loading schema from {schema_path}")
    schema = load_schema(schema_path)

    if not schema:
        logger.error("Failed to load schema.")
        sys.exit(1)

    logger.info("Generating model class from schema...")
    class_name = "AnalysisMetric"
    schema_name = "AnalysisMetricSchema"
    factory_name = "create_analysis_metric"

    # Generate the code content
    model_code = generate_model_class(
        class_name=class_name,
        schema_name=schema_name,
        factory_name=factory_name,
        schema_def=schema
    )

    if not model_code:
        logger.error("Model generation failed.")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    logger.info(f"Writing generated code to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(model_code)

    # Verify the generation
    logger.info("Verifying generated code against schema...")
    is_valid = verify_generation(output_path, schema, class_name)

    if not is_valid:
        logger.error("Verification failed. The generated code does not match the schema.")
        sys.exit(1)

    logger.info("T009e completed successfully. AnalysisMetric model generated and verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
