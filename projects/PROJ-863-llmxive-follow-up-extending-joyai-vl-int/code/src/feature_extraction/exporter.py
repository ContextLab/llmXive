import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict, is_dataclass
from src.utils.logging import get_logger
import hashlib
import time

def validate_feature_record(record: Dict[str, Any]) -> bool:
    """
    Validates that a feature record contains required fields for temporal alignment.
    Required fields:
      - frame_index: int
      - timestamp: float (Unix timestamp or relative seconds)
      - chunk_id: str
      - features: dict (the actual vector data)
    """
    required_keys = {"frame_index", "timestamp", "chunk_id", "features"}
    if not isinstance(record, dict):
        return False
    if not required_keys.issubset(record.keys()):
        return False
    if not isinstance(record["features"], dict):
        return False
    if not isinstance(record["frame_index"], int):
        return False
    if not isinstance(record["timestamp"], (int, float)):
        return False
    return True

def export_features_to_jsonl(
    features: List[Dict[str, Any]],
    output_path: str,
    manifest_path: Optional[str] = None,
    logger: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Exports a list of feature dictionaries to a JSONL file.
    Ensures temporal alignment metadata is preserved.
    
    Args:
        features: List of feature records (dicts) with temporal metadata.
        output_path: Path to the output .jsonl file.
        manifest_path: Optional path to write a manifest file.
        logger: Optional logger instance for audit logs.
        
    Returns:
        A dict containing export statistics (count, path, hash).
    """
    if logger is None:
        from src.utils.logging import get_logger
        logger = get_logger("feature_exporter")
        
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    valid_count = 0
    invalid_count = 0
    
    logger.info(f"Starting feature export to {output_path}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in features:
            if validate_feature_record(record):
                json_line = json.dumps(record)
                f.write(json_line + '\n')
                valid_count += 1
            else:
                invalid_count += 1
                logger.warning(f"Skipping invalid feature record: {record.get('frame_index', 'unknown')}")
                
    # Compute hash for integrity
    file_hash = compute_file_hash(output_file)
    
    result = {
        "output_path": str(output_file),
        "valid_records": valid_count,
        "invalid_records": invalid_count,
        "file_hash": file_hash
    }
    
    logger.info(f"Export complete. Valid: {valid_count}, Invalid: {invalid_count}")
    
    if manifest_path:
        generate_feature_manifest(result, manifest_path, logger)
        
    return result

def compute_file_hash(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_feature_manifest(
    export_stats: Dict[str, Any],
    manifest_path: str,
    logger: Optional[Any] = None
) -> None:
    """
    Generates a manifest.json file summarizing the feature export.
    """
    manifest = {
        "export_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_features": export_stats["valid_records"],
        "output_file": export_stats["output_path"],
        "file_hash": export_stats["file_hash"],
        "schema_version": "1.0.0",
        "metadata_keys": ["frame_index", "timestamp", "chunk_id", "features"]
    }
    
    manifest_file = Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        
    if logger:
        logger.info(f"Feature manifest written to {manifest_path}")

def main():
    """
    CLI entry point for exporting features.
    Expects a JSON file of features or a directory of JSONL chunks to consolidate.
    For this task, we demonstrate the export function with a sample structure
    that matches the output of the extractor (T021-T024).
    """
    from src.utils.logging import setup_project_logging
    import argparse
    
    setup_project_logging()
    logger = get_logger("exporter_main")
    
    parser = argparse.ArgumentParser(description="Export extracted features to JSONL")
    parser.add_argument("--input", type=str, required=True, help="Input JSON or JSONL file containing features")
    parser.add_argument("--output", type=str, required=True, help="Output JSONL file path")
    parser.add_argument("--manifest", type=str, default=None, help="Optional manifest output path")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Load input features
    # Support both single JSON list and JSONL input
    features = []
    if input_path.suffix == '.jsonl':
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    features.append(json.loads(line))
    elif input_path.suffix == '.json':
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                features = data
            else:
                features = [data]
    else:
        logger.error(f"Unsupported input format: {input_path.suffix}")
        return
        
    logger.info(f"Loaded {len(features)} features from {input_path}")
    
    # Export
    stats = export_features_to_jsonl(
        features=features,
        output_path=str(output_path),
        manifest_path=args.manifest,
        logger=logger
    )
    
    logger.info(f"Export statistics: {stats}")

if __name__ == "__main__":
    main()