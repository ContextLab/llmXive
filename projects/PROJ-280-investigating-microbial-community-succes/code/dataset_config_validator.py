import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml
import jsonschema
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load JSON schema from a YAML or JSON file.
    
    Args:
        schema_path: Path to the schema file (.yaml or .json)
        
    Returns:
        Dictionary containing the schema
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate_config(config_path: str, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a dataset configuration file against a JSON schema.
    
    Args:
        config_path: Path to the dataset configuration JSON file
        schema_path: Path to the JSON schema file
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    try:
        # Load schema
        schema = load_schema(schema_path)
        
        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate
        validator = jsonschema.Draft7Validator(schema)
        validation_errors = list(validator.iter_errors(config))
        
        if validation_errors:
            for error in validation_errors:
                error_path = ".".join(map(str, error.path)) if error.path else "root"
                errors.append(f"Error at '{error_path}': {error.message}")
        else:
            logger.info(f"Configuration '{config_path}' is valid.")
            
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in config file: {str(e)}")
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML in schema file: {str(e)}")
    except FileNotFoundError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Unexpected error during validation: {str(e)}")
    
    return (len(errors) == 0, errors)

def create_sample_config(output_path: str) -> None:
    """
    Create a sample dataset configuration file if one doesn't exist.
    
    Args:
        output_path: Path where the sample config should be written
    """
    sample_data = {
        "version": "1.0.0",
        "description": "Dataset configuration for microbial community succession study in constructed wetlands",
        "datasets": [
            {
                "id": "PRJNA555687",
                "source": "ncbi_sra",
                "description": "Constructed wetland microbiome time-series dataset",
                "metadata": {
                    "wetland_type": "constructed",
                    "nutrient_removal": True,
                    "target_nutrients": ["nitrogen", "phosphorus"],
                    "sampling_stages": ["early", "mid", "mature"],
                    "location": "North America",
                    "study_period": "24_months"
                }
            },
            {
                "id": "10.5281/zenodo.1234567",
                "source": "zenodo",
                "description": "Supplementary 16S rRNA feature tables from wetland study",
                "metadata": {
                    "wetland_type": "constructed",
                    "nutrient_removal": True,
                    "target_nutrients": ["nitrogen"],
                    "sampling_stages": ["early", "mature"],
                    "location": "Europe",
                    "study_period": "18_months"
                }
            }
        ]
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)
    
    logger.info(f"Sample configuration created at {output_path}")

def main():
    """Main entry point for the validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate dataset configuration against schema")
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='data/config/dataset_ids.json',
        help='Path to dataset configuration file'
    )
    parser.add_argument(
        '--schema', '-s',
        type=str,
        default='contracts/dataset-config.schema.yaml',
        help='Path to JSON schema file'
    )
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Create a sample configuration file'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/config/dataset_ids.json',
        help='Output path for sample configuration (if --create-sample is used)'
    )
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_config(args.output)
        return
    
    if not os.path.exists(args.config):
        logger.error(f"Configuration file not found: {args.config}")
        logger.info("Use --create-sample to generate a sample configuration.")
        return 1
    
    if not os.path.exists(args.schema):
        logger.error(f"Schema file not found: {args.schema}")
        return 1
    
    is_valid, errors = validate_config(args.config, args.schema)
    
    if is_valid:
        print(f"✓ Configuration is valid")
        return 0
    else:
        print("✗ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

if __name__ == "__main__":
    exit(main())
