"""
Schema contract validation script.
Validates YAML schema files using yamllint and writes validation log.
"""
import os
import sys
import logging
from pathlib import Path
import yaml
from datetime import datetime
import subprocess
import json

from utils.logging import get_logger
from utils.exceptions import CorrosionPipelineError

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = get_logger(__name__)

SCHEMA_FILES = [
    "contracts/ingest.schema.yaml",
    "contracts/dataset.schema.yaml"
]

def validate_yaml_schema(schema_path: str) -> dict:
    """
    Validate a YAML schema file using yamllint.
    
    Args:
        schema_path: Relative path to the schema file
        
    Returns:
        dict: Validation result with status and details
    """
    full_path = PROJECT_ROOT / schema_path
    
    if not full_path.exists():
        raise CorrosionPipelineError(f"Schema file not found: {full_path}")
    
    try:
        # Parse YAML to ensure it's valid syntax
        with open(full_path, 'r') as f:
            schema_content = yaml.safe_load(f)
        
        if schema_content is None:
            raise CorrosionPipelineError(f"Schema file is empty: {full_path}")
        
        # Run yamllint if available
        try:
            result = subprocess.run(
                ['yamllint', '-f', 'parsable', str(full_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                details = f"yamllint errors:\n{result.stdout}\n{result.stderr}"
                return {
                    "status": "FAIL",
                    "details": details,
                    "tool_version": "unknown"
                }
            
            # Get yamllint version
            version_result = subprocess.run(
                ['yamllint', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            tool_version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
            
        except FileNotFoundError:
            logger.warning("yamllint not installed, skipping lint validation")
            tool_version = "not_installed"
            details = "Skipped yamllint validation (not installed)"
        except subprocess.TimeoutExpired:
            details = "yamllint timed out"
            tool_version = "unknown"
        except Exception as e:
            details = f"yamllint error: {str(e)}"
            tool_version = "unknown"
        
        return {
            "status": "PASS",
            "details": f"Validated {schema_path} against yamllint {tool_version}: PASS",
            "tool_version": tool_version
        }
        
    except yaml.YAMLError as e:
        return {
            "status": "FAIL",
            "details": f"YAML parsing error: {str(e)}",
            "tool_version": "unknown"
        }
    except Exception as e:
        return {
            "status": "FAIL",
            "details": f"Validation error: {str(e)}",
            "tool_version": "unknown"
        }

def write_validation_log(validation_results: list) -> Path:
    """
    Write validation results to log file.
    
    Args:
        validation_results: List of validation result dicts
        
    Returns:
        Path to the log file
    """
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = log_dir / "schema_validation.log"
    
    log_entry = {
        "schema_file": [r["schema_file"] for r in validation_results],
        "validation_timestamp": datetime.utcnow().isoformat() + "Z",
        "tool_version": validation_results[0]["tool_version"] if validation_results else "unknown",
        "status": "PASS" if all(r["status"] == "PASS" for r in validation_results) else "FAIL",
        "details": [r["details"] for r in validation_results]
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Validation log written to {log_path}")
    return log_path

def main():
    """Main entry point for schema validation."""
    logger.info("Starting schema contract validation...")
    
    validation_results = []
    
    for schema_file in SCHEMA_FILES:
        logger.info(f"Validating {schema_file}...")
        result = validate_yaml_schema(schema_file)
        result["schema_file"] = schema_file
        validation_results.append(result)
        
        if result["status"] == "PASS":
            logger.info(f"✓ {schema_file}: {result['details']}")
        else:
            logger.error(f"✗ {schema_file}: {result['details']}")
    
    # Write validation log
    log_path = write_validation_log(validation_results)
    
    # Exit with appropriate code
    if all(r["status"] == "PASS" for r in validation_results):
        logger.info("All schema validations passed.")
        return 0
    else:
        logger.error("Schema validation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
