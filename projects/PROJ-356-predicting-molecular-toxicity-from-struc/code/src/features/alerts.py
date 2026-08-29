"""
Alert feature extraction and validation module.

This module handles:
1. Loading and validating structural alert configurations against a schema.
2. Compiling SMARTS patterns for efficient matching.
3. Generating binary feature vectors indicating the presence of alerts in molecules.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import yaml
from rdkit import Chem
from rdkit.Chem import AllChem

# Configure logger for this module
logger = logging.getLogger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load the validation schema from a YAML file.

    Args:
        schema_path: Path to the alerts.schema.yaml file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    logger.info(f"Loaded schema from {schema_path}")
    return schema


def validate_alert_config(config: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a structural alert configuration against a schema.

    This function checks:
    1. The top-level 'patterns' key exists and is a list.
    2. Each pattern contains required fields: 'pattern_id', 'smarts_string', 'weight'.
    3. Each pattern contains optional but recommended fields: 'source', 'description'.
    4. The 'smarts_string' is a valid SMARTS pattern using RDKit.
    5. The 'weight' is a positive number.
    6. 'pattern_id' is unique across all patterns.

    Args:
        config: The loaded JSON configuration dictionary.
        schema: The loaded YAML schema dictionary.

    Returns:
        A tuple (is_valid, errors) where is_valid is a boolean and errors is a list of error messages.
    """
    errors = []
    required_fields = schema.get('required_fields', ['pattern_id', 'smarts_string', 'weight'])
    optional_fields = schema.get('optional_fields', ['source', 'description'])

    # Check top-level structure
    if 'patterns' not in config:
        errors.append("Configuration missing 'patterns' key.")
        return False, errors

    patterns = config['patterns']
    if not isinstance(patterns, list):
        errors.append("'patterns' must be a list.")
        return False, errors

    if len(patterns) == 0:
        errors.append("'patterns' list is empty. At least one alert pattern is required.")
        return False, errors

    seen_ids = set()

    for idx, pattern in enumerate(patterns):
        if not isinstance(pattern, dict):
            errors.append(f"Pattern at index {idx} is not a dictionary.")
            continue

        # Check required fields
        for field in required_fields:
            if field not in pattern:
                errors.append(f"Pattern at index {idx} missing required field: '{field}'.")

        # Check optional fields presence (logging warning if missing)
        for field in optional_fields:
            if field not in pattern:
                logger.warning(f"Pattern at index {idx} missing optional field: '{field}'.")

        # Validate SMARTS string
        if 'smarts_string' in pattern:
            smarts = pattern['smarts_string']
            try:
                mol_pattern = Chem.MolFromSmarts(smarts)
                if mol_pattern is None:
                    errors.append(f"Pattern '{pattern.get('pattern_id', idx)}': Invalid SMARTS string '{smarts}'.")
            except Exception as e:
                errors.append(f"Pattern '{pattern.get('pattern_id', idx)}': Error parsing SMARTS '{smarts}': {str(e)}")

        # Validate weight
        if 'weight' in pattern:
            try:
                weight = float(pattern['weight'])
                if weight <= 0:
                    errors.append(f"Pattern '{pattern.get('pattern_id', idx)}': Weight must be positive, got {weight}.")
            except (ValueError, TypeError):
                errors.append(f"Pattern '{pattern.get('pattern_id', idx)}': Weight must be a number.")

        # Check uniqueness of pattern_id
        if 'pattern_id' in pattern:
            pid = pattern['pattern_id']
            if pid in seen_ids:
                errors.append(f"Duplicate pattern_id found: '{pid}'.")
            else:
                seen_ids.add(pid)

    is_valid = len(errors) == 0
    return is_valid, errors


def load_and_validate_alerts(config_path: Path, schema_path: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Load the alert configuration and validate it against the schema.

    Args:
        config_path: Path to the structural_alerts.json file.
        schema_path: Path to the alerts.schema.yaml file.

    Returns:
        A tuple (config, errors). If validation passes, config is the loaded dictionary and errors is empty.
        If validation fails, config is None and errors contains the list of error messages.
    """
    # Load schema
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return None, [str(e)]
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in schema: {e}")
        return None, [f"Invalid YAML in schema: {e}"]

    # Load config
    if not config_path.exists():
        error_msg = f"Config file not found: {config_path}"
        logger.error(error_msg)
        return None, [error_msg]

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in config file: {e}"
        logger.error(error_msg)
        return None, [error_msg]

    # Validate
    is_valid, errors = validate_alert_config(config, schema)

    if not is_valid:
        logger.error(f"Validation failed with {len(errors)} errors:")
        for err in errors:
            logger.error(f"  - {err}")
        return None, errors

    logger.info("Alert configuration validated successfully.")
    return config, []


def compile_patterns(patterns: List[Dict[str, Any]]) -> List[Tuple[str, Any]]:
    """
    Compile SMARTS strings into RDKit Mol objects.

    Args:
        patterns: List of pattern dictionaries containing 'pattern_id' and 'smarts_string'.

    Returns:
        List of tuples (pattern_id, compiled_mol_object).
    """
    compiled = []
    for p in patterns:
        smarts = p['smarts_string']
        pid = p['pattern_id']
        mol = Chem.MolFromSmarts(smarts)
        if mol is not None:
            compiled.append((pid, mol))
        else:
            # This should ideally not happen if validation passed, but safety check
            logger.warning(f"Failed to compile SMARTS for {pid}: {smarts}")
    return compiled


def generate_alert_vectors(molecules: List[Chem.Mol], compiled_patterns: List[Tuple[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate binary feature vectors indicating the presence of each alert in a molecule.

    Args:
        molecules: List of RDKit Mol objects.
        compiled_patterns: List of (pattern_id, mol_pattern) tuples.

    Returns:
        List of dictionaries, one per molecule, with keys 'smiles' (if available) and
        keys for each pattern_id with value 1 (match) or 0 (no match).
    """
    results = []
    pattern_ids = [pid for pid, _ in compiled_patterns]

    for mol in molecules:
        if mol is None:
            continue

        # Try to get SMILES for identification
        smiles = Chem.MolToSmiles(mol)

        feature_vec = {'smiles': smiles}
        for pid, mol_pattern in compiled_patterns:
            if mol.HasSubstructMatch(mol_pattern):
                feature_vec[pid] = 1
            else:
                feature_vec[pid] = 0
        results.append(feature_vec)

    return results


def main():
    """
    Main entry point for script execution.
    Validates the alert configuration file and prints results.
    """
    # Define paths relative to project root
    # Assuming this script is run from the project root or code directory
    project_root = Path(__file__).resolve().parent.parent.parent
    config_path = project_root / "config" / "structural_alerts.json"
    schema_path = project_root / "contracts" / "alerts.schema.yaml"

    print(f"Checking paths:")
    print(f"  Config: {config_path}")
    print(f"  Schema: {schema_path}")

    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        return 1

    if not schema_path.exists():
        print(f"ERROR: Schema file not found at {schema_path}")
        return 1

    config, errors = load_and_validate_alerts(config_path, schema_path)

    if errors:
        print(f"Validation FAILED with {len(errors)} errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("Validation PASSED.")
    if config:
        print(f"Loaded {len(config.get('patterns', []))} patterns.")
        # Optionally compile them to ensure they work
        compiled = compile_patterns(config['patterns'])
        print(f"Successfully compiled {len(compiled)} patterns.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
