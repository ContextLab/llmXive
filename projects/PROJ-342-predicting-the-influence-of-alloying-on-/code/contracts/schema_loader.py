import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass

class BaseSchemaLoader:
    """Base class for schema loaders."""
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the schema loader.
        
        Args:
            schema_path: Path to the schema file. If None, uses default.
        """
        self.schema_path = schema_path or self._find_schema_path()
        self.schema = self._load_schema()
        
    def _find_schema_path(self) -> str:
        """Find the schema file."""
        possible_paths = [
            "code/contracts/dataset.schema.yaml",
            "specs/001-predict-tg-metallic-glasses/contracts/dataset.schema.yaml",
            "dataset.schema.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Create a minimal default schema
        return self._create_default_schema()
        
    def _create_default_schema(self) -> str:
        """Create a default schema file."""
        default_schema = {
            "type": "object",
            "properties": {
                "Tg": {"type": "number"},
                "composition": {"type": "string"}
            },
            "required": ["Tg", "composition"]
        }
        
        schema_path = "code/contracts/dataset.schema.yaml"
        os.makedirs(os.path.dirname(schema_path), exist_ok=True)
        
        with open(schema_path, 'w') as f:
            yaml.dump(default_schema, f, default_flow_style=False)
        
        return schema_path
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the schema from file."""
        try:
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            return schema if schema else {}
        except Exception as e:
            raise SchemaValidationError(f"Failed to load schema from {self.schema_path}: {str(e)}")
            
    def validate(self, data: Any) -> bool:
        """
        Validate data against the schema.
        
        Args:
            data: The data to validate.
            
        Returns:
            True if valid.
            
        Raises:
            SchemaValidationError: If validation fails.
        """
        raise NotImplementedError("Subclasses must implement validate method")

class DatasetSchemaLoader(BaseSchemaLoader):
    """Schema loader for dataset validation."""
    
    def _find_schema_path(self) -> str:
        """Find the dataset schema file."""
        possible_paths = [
            "code/contracts/dataset.schema.yaml",
            "specs/001-predict-tg-metallic-glasses/contracts/dataset.schema.yaml",
            "dataset.schema.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return self._create_default_schema()
        
    def validate(self, data: Any) -> bool:
        """
        Validate a DataFrame against the dataset schema.
        
        Args:
            data: The DataFrame to validate.
            
        Returns:
            True if valid.
            
        Raises:
            SchemaValidationError: If validation fails.
        """
        try:
            import pandas as pd
            
            if not isinstance(data, pd.DataFrame):
                raise SchemaValidationError("Data must be a pandas DataFrame")
            
            schema = self.schema
            
            # Check required columns
            if 'required' in schema:
                required_cols = schema['required']
                missing_cols = [col for col in required_cols if col not in data.columns]
                if missing_cols:
                    raise SchemaValidationError(f"Missing required columns: {missing_cols}")
            
            # Check column types
            if 'properties' in schema:
                for col, spec in schema['properties'].items():
                    if col in data.columns:
                        if spec.get('type') == 'number':
                            if not pd.api.types.is_numeric_dtype(data[col]):
                                raise SchemaValidationError(f"Column '{col}' must be numeric")
                        elif spec.get('type') == 'string':
                            if not pd.api.types.is_string_dtype(data[col]):
                                raise SchemaValidationError(f"Column '{col}' must be string")
            
            return True
            
        except SchemaValidationError:
            raise
        except Exception as e:
            raise SchemaValidationError(f"Validation error: {str(e)}")

class ArtifactSchemaLoader(BaseSchemaLoader):
    """Schema loader for artifact validation."""
    
    def _find_schema_path(self) -> str:
        """Find the artifact schema file."""
        possible_paths = [
            "code/contracts/artifact.schema.yaml",
            "specs/001-predict-tg-metallic-glasses/contracts/artifact.schema.yaml",
            "artifact.schema.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return self._create_default_schema()
        
    def validate(self, data: Any) -> bool:
        """
        Validate an artifact against the schema.
        
        Args:
            data: The artifact data to validate.
            
        Returns:
            True if valid.
            
        Raises:
            SchemaValidationError: If validation fails.
        """
        try:
            if not isinstance(data, dict):
                raise SchemaValidationError("Artifact data must be a dictionary")
            
            schema = self.schema
            
            # Check required fields
            if 'required' in schema:
                required_fields = schema['required']
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise SchemaValidationError(f"Missing required fields: {missing_fields}")
            
            return True
            
        except SchemaValidationError:
            raise
        except Exception as e:
            raise SchemaValidationError(f"Validation error: {str(e)}")

def load_dataset_schema(schema_path: Optional[str] = None) -> DatasetSchemaLoader:
    """
    Load the dataset schema.
    
    Args:
        schema_path: Optional path to the schema file.
        
    Returns:
        A DatasetSchemaLoader instance.
    """
    return DatasetSchemaLoader(schema_path)

def load_artifact_schema(schema_path: Optional[str] = None) -> ArtifactSchemaLoader:
    """
    Load the artifact schema.
    
    Args:
        schema_path: Optional path to the schema file.
        
    Returns:
        An ArtifactSchemaLoader instance.
    """
    return ArtifactSchemaLoader(schema_path)

def main():
    """Main function for testing schema loaders."""
    print("Testing DatasetSchemaLoader...")
    dataset_loader = load_dataset_schema()
    print(f"Dataset schema loaded from: {dataset_loader.schema_path}")
    
    print("\nTesting ArtifactSchemaLoader...")
    artifact_loader = load_artifact_schema()
    print(f"Artifact schema loaded from: {artifact_loader.schema_path}")
    
    return dataset_loader, artifact_loader

if __name__ == "__main__":
    main()
