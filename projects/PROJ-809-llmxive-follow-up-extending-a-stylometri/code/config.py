import json
import os
import random
import re
from pathlib import Path
from typing import Any, Dict, Optional, List

import yaml

# Project Root Path (relative to where scripts are run)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
SEED_FILE = PROJECT_ROOT / "state" / "seed_state.json"

# Global seed state
_seed_state = {
    "global_seed": 42,
    "ngram_seed": 42,
    "sampling_seed": 42,
    "base_seed": 42
}

def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    path = config_path or CONFIG_PATH
    if not path.exists():
        # Return defaults if config doesn't exist yet
        return {
            "project": "llmXive-followup",
            "version": "1.0.0",
            "seeds": {
                "global": 42,
                "ngram": 42,
                "sampling": 42
            },
            "paths": {
                "raw_data": "data/raw",
                "processed_data": "data/processed",
                "hybrid_data": "data/hybrid",
                "models": "artifacts/models",
                "metrics": "artifacts/metrics",
                "results": "artifacts/results"
            },
            "data_ingestion": {
                "categories": ["cs.CL", "physics.gen-ph", "q-bio.QM"],
                "min_authors": 20,
                "min_abstracts_per_author": 10,
                "min_abstract_length": 6
            },
            "model_training": {
                "ngram_orders": [4, 5, 6],
                "kneser_ney_smoothing": True,
                "train_test_split": 0.2,
                "sparsity_threshold": 0.95
            },
            "evaluation": {
                "primary_ngram_order": 5,
                "baseline_method": "function_words",
                "statistical_test": "mcnemar"
            }
        }
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """Save configuration to YAML file."""
    path = config_path or CONFIG_PATH
    ensure_dir(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def set_seed(seed_name: str, seed_value: int) -> None:
    """Set a specific seed value."""
    _seed_state[seed_name] = seed_value
    # Also update global seed if this is the global seed
    if seed_name == "global_seed":
        random.seed(seed_value)
        os.environ['PYTHONHASHSEED'] = str(seed_value)

def get_seed(seed_name: str) -> int:
    """Get a specific seed value."""
    return _seed_state.get(seed_name, _seed_state["base_seed"])

def reset_config() -> None:
    """Reset seeds to default values."""
    global _seed_state
    _seed_state = {
        "global_seed": 42,
        "ngram_seed": 42,
        "sampling_seed": 42,
        "base_seed": 42
    }

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON schema from the contracts directory."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_against_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Basic validation of data against a JSON schema.
    Note: This is a simplified validator. For production, use jsonschema library.
    """
    schema_type = schema.get("type")
    
    if schema_type == "object":
        if not isinstance(data, dict):
            return False
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for key in required:
            if key not in data:
                return False
        
        for key, value in data.items():
            if key in properties:
                if not validate_against_schema(value, properties[key]):
                    return False
        return True
    
    elif schema_type == "array":
        if not isinstance(data, list):
            return False
        items_schema = schema.get("items", {})
        for item in data:
            if not validate_against_schema(item, items_schema):
                return False
        return True
    
    elif schema_type == "string":
        return isinstance(data, str)
    
    elif schema_type == "number":
        return isinstance(data, (int, float))
    
    elif schema_type == "integer":
        return isinstance(data, int)
    
    elif schema_type == "boolean":
        return isinstance(data, bool)
    
    elif schema_type == "null":
        return data is None
    
    return True

def get_contract_paths() -> List[Path]:
    """Get all schema paths in the contracts directory."""
    if not CONTRACTS_DIR.exists():
        return []
    
    contract_paths = []
    for pattern in ["*.json", "*.yaml", "*.yml"]:
        contract_paths.extend(CONTRACTS_DIR.glob(pattern))
    
    return sorted(contract_paths)

def main():
    """Main entry point for configuration management."""
    print("llmXive Configuration Loader")
    print("=" * 40)
    
    # Load or create config
    config = load_config()
    print(f"Loaded config from: {CONFIG_PATH}")
    print(f"Project: {config.get('project', 'Unknown')}")
    print(f"Version: {config.get('version', 'Unknown')}")
    
    # Show seed values
    print("\nCurrent Seeds:")
    for key, value in _seed_state.items():
        print(f"  {key}: {value}")
    
    # Show contract paths
    contracts = get_contract_paths()
    print(f"\nFound {len(contracts)} contract schemas:")
    for c in contracts:
        print(f"  - {c.relative_to(PROJECT_ROOT)}")
    
    # Example: Load and validate a schema
    if contracts:
        first_schema_path = contracts[0]
        try:
            schema = load_schema(first_schema_path)
            print(f"\nSuccessfully loaded schema: {first_schema_path.name}")
            print(f"Schema type: {schema.get('type', 'unknown')}")
        except Exception as e:
            print(f"Error loading schema: {e}")
    
    # Example: Validate sample data
    sample_data = {"test": "value", "number": 42}
    test_schema = {"type": "object", "properties": {"test": {"type": "string"}}, "required": ["test"]}
    is_valid = validate_against_schema(sample_data, test_schema)
    print(f"\nSample data validation: {'PASSED' if is_valid else 'FAILED'}")

if __name__ == "__main__":
    main()