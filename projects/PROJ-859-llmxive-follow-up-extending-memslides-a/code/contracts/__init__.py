"""
Contract validation logic for the llmXive project.
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from config import get_config

class SchemaValidator:
    """Base class for schema validation."""
    def __init__(self, schema_path: Path, config=None):
        self.config = config or get_config()
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """Load the YAML schema from disk."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def validate_json_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate a JSON file against the loaded schema.
        
        Args:
            file_path: Path to the JSON file to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        
        # Basic validation: check if required keys from schema exist
        # A full implementation would use jsonschema library for deep validation
        required_keys = self.schema.get("required", [])
        missing_keys = [k for k in required_keys if k not in data]
        
        if missing_keys:
            return False, f"Missing required keys: {missing_keys}"
        
        return True, None

class TraceValidator(SchemaValidator):
    """Validator for trace schema."""
    def __init__(self, config=None):
        super().__init__(config.config_dir / "trace.schema.yaml", config)

class MetricsValidator(SchemaValidator):
    """Validator for metrics schema."""
    def __init__(self, config=None):
        super().__init__(config.config_dir / "metrics.schema.yaml", config)

class BenchmarkResultsValidator(SchemaValidator):
    """Validator for benchmark results schema."""
    def __init__(self, config=None):
        super().__init__(config.config_dir / "benchmark_results.schema.yaml", config)

class CompressibilityAnalysisValidator(SchemaValidator):
    """Validator for compressibility analysis schema."""
    def __init__(self, config=None):
        super().__init__(config.config_dir / "compressibility_analysis.schema.yaml", config)
