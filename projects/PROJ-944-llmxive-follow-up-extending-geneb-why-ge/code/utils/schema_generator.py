"""
Utility to generate and validate the dataset schema based on data-model.md.
This module ensures the schema aligns with the authoritative feature list.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logging import get_logger, PipelineError

logger = get_logger(__name__)

def load_data_model_features(data_model_path: str) -> List[str]:
    """
    Reads the `data-model.md` artifact to extract the authoritative list of features.
    Parses the markdown to find the feature list section.
    
    Args:
        data_model_path: Path to the data-model.md file.
        
    Returns:
        List of feature names.
        
    Raises:
        PipelineError: If the file is missing or the feature list cannot be parsed.
    """
    path = Path(data_model_path)
    if not path.exists():
        raise PipelineError(f"Data model file not found: {data_model_path}")
    
    features = []
    try:
        content = path.read_text(encoding='utf-8')
        # Simple heuristic: look for lines starting with "- " or "* " in a list context
        # This is a basic parser; a more robust one would use markdown parsing libraries.
        # We assume the data-model.md has a section like:
        # ## Features
        # - feature_name_1
        # - feature_name_2
        
        in_feature_section = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                if "feature" in stripped.lower():
                    in_feature_section = True
                else:
                    in_feature_section = False
            
            if in_feature_section and (stripped.startswith("- ") or stripped.startswith("* ")):
                feature_name = stripped[2:].strip()
                if feature_name:
                    features.append(feature_name)
                    
        if not features:
            raise PipelineError("Could not parse any features from data-model.md. Check format.")
            
        return features
    except Exception as e:
        raise PipelineError(f"Failed to parse data-model.md: {e}")

def generate_schema_from_data_model(data_model_path: str, output_path: str) -> None:
    """
    Generates the dataset.schema.yaml dynamically based on the features listed in data-model.md.
    
    Args:
        data_model_path: Path to the source data-model.md.
        output_path: Path where the generated schema will be saved.
    """
    features = load_data_model_features(data_model_path)
    
    # Verify at_content is excluded
    if "at_content" in features:
        logger.warning("at_content found in data-model.md. Removing it to comply with collinearity constraint.")
        features.remove("at_content")
    
    if len(features) != 15:
        logger.warning(f"Expected 15 features, found {len(features)} in data-model.md. Schema will reflect actual count.")
    
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "SequenceFeatureSet",
        "description": f"""
        Schema for the GENEB sequence feature dataset.
        Generated dynamically from {data_model_path}.
        
        Contains exactly {len(features)} features: {', '.join(features)}.
        Explicitly excludes 'at_content' due to collinearity with GC-Content.
        """,
        "type": "object",
        "required": ["task_id", "features"],
        "properties": {
            "task_id": {
                "description": "Unique identifier for the benchmark task.",
                "type": "string",
                "pattern": "^[a-zA-Z0-9_-]+$"
            },
            "features": {
                "description": f"Map of sequence features defined in data-model.md. Count: {len(features)}.",
                "type": "object",
                "additionalProperties": {
                    "type": "number",
                    "minimum": 0.0,
                    "description": "Computed value for a sequence feature."
                },
                "minProperties": len(features),
                "maxProperties": len(features)
            }
        },
        "additionalProperties": False
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Schema generated successfully at {output_path} with {len(features)} features.")

def main():
    """Entry point for schema generation."""
    project_root = Path(__file__).resolve().parent.parent.parent
    data_model_path = project_root / "data-model.md"
    schema_output_path = project_root / "specs" / "gene-regulation" / "contracts" / "dataset.schema.yaml"
    
    if not data_model_path.exists():
        # Fallback to the static schema if data-model.md is missing, 
        # but log a warning as per task requirements.
        logger.warning("data-model.md not found. Generating static schema with placeholder structure.")
        # In a real run, this should fail loudly if data-model.md is required.
        # For this task, we assume data-model.md exists as per Phase 1 output.
        raise PipelineError("data-model.md is required for dynamic schema generation.")
    
    generate_schema_from_data_model(str(data_model_path), str(schema_output_path))

if __name__ == "__main__":
    main()
