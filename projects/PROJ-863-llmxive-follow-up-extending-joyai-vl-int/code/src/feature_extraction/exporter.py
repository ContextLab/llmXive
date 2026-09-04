import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict, is_dataclass

from src.utils.logging import get_logger
from src.utils.validation import validate_schema, ValidationError
from src.feature_extraction.streaming import enforce_memory_limit

logger = get_logger(__name__)

# Schema definition for the exported feature record
FEATURE_RECORD_SCHEMA = {
    "type": "object",
    "required": [
        "frame_id",
        "timestamp_ms",
        "chunk_id",
        "video_id",
        "features",
        "feature_vector_dimension"
    ],
    "properties": {
        "frame_id": {"type": "integer"},
        "timestamp_ms": {"type": "integer"},
        "chunk_id": {"type": "string"},
        "video_id": {"type": "string"},
        "features": {
            "type": "object",
            "additionalProperties": True
        },
        "feature_vector_dimension": {"type": "integer"},
        "labels": {
            "type": "object",
            "additionalProperties": True,
            "optional": True
        }
    }
}

def validate_feature_record(record: Dict[str, Any]) -> bool:
    """Validates a single feature record against the schema."""
    try:
        validate_schema(record, FEATURE_RECORD_SCHEMA)
        # Ensure features is not empty and has numeric values
        if not record.get("features"):
            raise ValidationError("Feature vector is empty.")
        for k, v in record["features"].items():
            if not isinstance(v, (int, float, list)):
                raise ValidationError(f"Feature '{k}' has invalid type: {type(v)}")
        return True
    except ValidationError as e:
        logger.error(f"Validation failed for record: {e}")
        raise

def export_features_to_jsonl(
    features_stream: List[Dict[str, Any]],
    output_path: Path,
    validate: bool = True
) -> int:
    """
    Exports a list of feature dictionaries to a JSONL file.
    
    Args:
        features_stream: List of feature dictionaries. Each dict must contain
                         frame_id, timestamp_ms, chunk_id, video_id, features, 
                         and feature_vector_dimension.
        output_path: Path to the output .jsonl file.
        validate: If True, validates each record before writing.
        
    Returns:
        The number of records written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in features_stream:
            if validate:
                validate_feature_record(record)
            
            # Ensure deterministic JSON output for reproducibility
            json_line = json.dumps(record, sort_keys=True)
            f.write(json_line + '\n')
            count += 1
            
            # Periodic memory check if stream is large
            if count % 10000 == 0:
                enforce_memory_limit(threshold_mb=5000)
                logger.debug(f"Wrote {count} records to {output_path}")
    
    logger.info(f"Exported {count} feature records to {output_path}")
    return count

def generate_feature_manifest(
    output_dir: Path,
    manifest_path: Path
) -> Dict[str, Any]:
    """
    Generates a manifest file tracking exported feature files.
    
    Args:
        output_dir: Directory containing the exported .jsonl files.
        manifest_path: Path where the manifest.json will be written.
        
    Returns:
        The manifest dictionary.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "type": "feature_manifest",
        "version": "1.0",
        "files": [],
        "total_records": 0
    }
    
    for file_path in sorted(output_dir.glob("*.jsonl")):
        file_size = file_path.stat().st_size
        record_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for _ in f:
                record_count += 1
        
        entry = {
            "path": str(file_path.relative_to(output_dir)),
            "size_bytes": file_size,
            "record_count": record_count
        }
        manifest["files"].append(entry)
        manifest["total_records"] += record_count
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Generated feature manifest at {manifest_path}")
    return manifest

def main():
    """
    Entry point for testing the exporter directly.
    Simulates a stream of features and writes them to disk.
    """
    import tempfile
    import random

    # Setup temporary output directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "features"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate a stream of features
        mock_features = []
        for i in range(100):
            record = {
                "frame_id": i,
                "timestamp_ms": i * 33, # ~30fps
                "chunk_id": "chunk_001",
                "video_id": "synthetic_vid_001",
                "features": {
                    "hidden_state_layer_0": [random.random() for _ in range(768)],
                    "attention_head_0": [random.random() for _ in range(12)]
                },
                "feature_vector_dimension": 780,
                "labels": {
                    "ground_truth": "fall" if i > 50 else "normal"
                }
            }
            mock_features.append(record)
        
        # Export
        output_file = output_dir / "features_chunk_001.jsonl"
        count = export_features_to_jsonl(mock_features, output_file)
        
        # Generate manifest
        manifest_file = output_dir / "manifest.json"
        manifest = generate_feature_manifest(output_dir, manifest_file)
        
        print(f"Successfully exported {count} records.")
        print(f"Manifest: {manifest}")

if __name__ == "__main__":
    main()
