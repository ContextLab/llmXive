"""
Task T047: Validate results/stats.json against contracts/results_schema.yaml.

This script loads the generated statistical results and validates them against
the JSON schema defined in contracts/results_schema.yaml.
"""
import os
import sys
import json
import logging
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema package is required. Install with: pip install jsonschema")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> dict:
    """Load the JSON schema from a YAML or JSON file."""
    # Simple YAML loader for basic schema (no external deps if possible)
    # If the file is actually YAML, we might need PyYAML.
    # Given the constraint to use real deps, we assume jsonschema handles the validation
    # and we load the schema content. If it's YAML, we need to parse it.
    # For robustness, we check extension.
    with open(schema_path, 'r') as f:
        content = f.read()
    
    if schema_path.suffix in ['.yaml', '.yml']:
        try:
            import yaml
            return yaml.safe_load(content)
        except ImportError:
            logger.error("PyYAML is required to load YAML schemas. Install with: pip install pyyaml")
            sys.exit(1)
    else:
        return json.loads(content)

def validate_results(stats_path: Path, schema_path: Path) -> bool:
    """Validate the stats.json file against the schema."""
    logger.info(f"Loading schema from: {schema_path}")
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return False

    schema = load_schema(schema_path)

    logger.info(f"Loading results from: {stats_path}")
    if not stats_path.exists():
        logger.error(f"Results file not found: {stats_path}")
        return False

    with open(stats_path, 'r') as f:
        data = json.load(f)

    logger.info("Validating data against schema...")
    try:
        jsonschema.validate(instance=data, schema=schema)
        logger.info("VALIDATION SUCCESSFUL: results/stats.json conforms to the schema.")
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"VALIDATION FAILED: {e.message}")
        logger.error(f"Path: {list(e.path)}")
        logger.error(f"Instance: {e.instance}")
        return False
    except jsonschema.SchemaError as e:
        logger.error(f"SCHEMA ERROR: {e.message}")
        return False

def main():
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    results_file = project_root / "results" / "stats.json"
    schema_file = project_root / "contracts" / "results_schema.yaml"

    if not results_file.exists():
        logger.error(f"Results file does not exist: {results_file}")
        logger.error("Ensure the statistical analysis pipeline (T037-T044) has been run first.")
        sys.exit(1)

    success = validate_results(results_file, schema_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
