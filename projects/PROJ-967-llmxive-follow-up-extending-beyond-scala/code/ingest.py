import argparse
import hashlib
import logging
import os
import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import requests
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Setup & Download Functions ---

def setup_directories():
    """Create necessary directories for data processing."""
    dirs = ["data/raw", "data/processed", "code", "tests", "results"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {d}")

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(url: str, output_path: str, expected_checksum: Optional[str] = None) -> bool:
    """Download dataset from URL and verify checksum if provided."""
    logger.info(f"Downloading dataset from {url} to {output_path}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if expected_checksum:
            actual_checksum = calculate_sha256(output_path)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}")
                return False
        logger.info("Download and verification complete.")
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def validate_schema(filepath: str) -> bool:
    """Validate the schema of the downloaded dataset."""
    required_columns = ["sample_id", "prompt", "teacher_logits", "student_score", "human_annotations"]
    rubric_dims = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not all(col in headers for col in required_columns):
                logger.error(f"Missing required columns. Found: {headers}")
                return False
            
            # Check human_annotations format (simplified check)
            # Assuming human_annotations is a JSON string in the CSV
            first_row = next(reader)
            try:
                annotations = json.loads(first_row["human_annotations"])
                if not all(dim in annotations for dim in rubric_dims):
                    logger.error(f"Missing rubric dimensions in annotations. Found: {list(annotations.keys())}")
                    return False
            except json.JSONDecodeError:
                logger.error("Invalid JSON in human_annotations column.")
                return False
            
            logger.info("Schema validation passed.")
            return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False

# --- Data Loading & Alignment ---

def identify_primary_quality_dimension(metadata: Dict[str, Any]) -> str:
    """Identify the primary quality dimension based on prompt metadata."""
    # Placeholder logic: default to 'Alignment' if no specific metadata is found
    # In a real scenario, this would parse the metadata dict provided in the dataset
    return metadata.get("primary_dimension", "Alignment")

def load_and_align_data(filepath: str, output_path: str) -> Dict[str, Any]:
    """
    Load the raw CSV, align teacher/student/human data by sample ID,
    and output a structured JSON for downstream processing.
    """
    logger.info(f"Loading and aligning data from {filepath}")
    aligned_samples = []
    missing_data_flags = []
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                sample_id = row["sample_id"]
                prompt = row["prompt"]
                
                # Parse teacher logits (assuming JSON string in CSV)
                teacher_logits = json.loads(row["teacher_logits"])
                # Ensure consistent order for rubric dimensions
                rubric_order = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
                teacher_dist = {k: teacher_logits.get(k, 0.0) for k in rubric_order}
                
                # Parse student score
                student_score = float(row["student_score"])
                
                # Parse human annotations
                human_annotations = json.loads(row["human_annotations"])
                
                # Identify primary dimension
                primary_dim = identify_primary_quality_dimension({"sample_id": sample_id, "prompt": prompt})
                
                # Check for missing data
                has_missing = any(np.isnan(human_annotations.get(k, np.nan)) for k in rubric_order)
                if has_missing:
                    missing_data_flags.append(sample_id)
                
                aligned_sample = {
                    "sample_id": sample_id,
                    "prompt": prompt,
                    "teacher_distribution": teacher_dist,
                    "student_score": student_score,
                    "human_annotations": human_annotations,
                    "primary_quality_dimension": primary_dim,
                    "has_missing_data": has_missing
                }
                aligned_samples.append(aligned_sample)
            except Exception as e:
                logger.warning(f"Skipping malformed row {row.get('sample_id', 'unknown')}: {e}")
                continue
    
    output_data = {
        "total_samples": len(aligned_samples),
        "missing_data_samples": len(missing_data_flags),
        "samples": aligned_samples
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Aligned data saved to {output_path}")
    return output_data

def print_summary(data: Dict[str, Any]):
    """Print a summary of the aligned dataset."""
    print(f"Total Samples: {data['total_samples']}")
    print(f"Samples with Missing Data: {data['missing_data_samples']}")
    if data['samples']:
        first = data['samples'][0]
        print(f"Rubric Dimensions: {list(first['teacher_distribution'].keys())}")
        print(f"Example Primary Dimension: {first['primary_quality_dimension']}")

# --- CLI Entry Point ---

def parse_args():
    parser = argparse.ArgumentParser(description="Ingest and align Z-Reward dataset.")
    parser.add_argument(
        "--url", "-u",
        type=str,
        default="https://huggingface.co/datasets/llmXive/zreward/raw/main/zreward_dataset.csv",
        help="URL to the Z-Reward dataset"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/processed/aligned_data.json",
        help="Path to save the aligned data JSON"
    )
    parser.add_argument(
        "--raw", "-r",
        type=str,
        default="data/raw/zreward_dataset.csv",
        help="Path to save the raw downloaded CSV"
    )
    parser.add_argument(
        "--checksum", "-c",
        type=str,
        default=None,
        help="Expected SHA256 checksum (optional)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    setup_directories()
    
    if not os.path.exists(args.raw):
        success = download_dataset(args.url, args.raw, args.checksum)
        if not success:
            logger.error("Dataset download failed. Exiting.")
            sys.exit(1)
    
    if not validate_schema(args.raw):
        logger.error("Schema validation failed. Exiting.")
        sys.exit(1)
    
    data = load_and_align_data(args.raw, args.output)
    print_summary(data)
    logger.info("Ingestion pipeline completed.")

if __name__ == "__main__":
    main()
