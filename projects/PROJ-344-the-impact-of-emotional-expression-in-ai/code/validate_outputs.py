"""
T028: Validate all output artifacts (CSV, JSON, PNG) against schemas and success criteria.

This script validates:
1. CSV files against the dataset schema (FR-001)
2. JSON files against the feature extraction schema
3. PNG files for existence, non-zero size, and valid image header
4. Content validation for consistency scores, trust scores, and correlation results
"""
import os
import sys
import csv
import json
import yaml
import struct
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from validators import load_schema, validate_schema_compliance, ValidationError
from logging_config import get_logger, setup_logging
from config import PROJECT_ROOT

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Define expected output paths based on completed tasks
OUTPUT_CSV_PATH = os.path.join(PROJECT_ROOT, "data/processed/consistency_results.csv")
OUTPUT_JSON_PATH = os.path.join(PROJECT_ROOT, "outputs/analysis_results.json")
OUTPUT_PNG_PATH = os.path.join(PROJECT_ROOT, "outputs/scatter_plot.png")

SCHEMA_PATH_DATASET = os.path.join(PROJECT_ROOT, "specs/001-emotional-synchrony-trust/contracts/dataset_schema.yaml")
SCHEMA_PATH_FEATURES = os.path.join(PROJECT_ROOT, "specs/001-emotional-synchrony-trust/contracts/feature_extraction_schema.yaml")

def validate_csv_schema(file_path: str, schema_path: str) -> bool:
    """Validate CSV file against dataset schema."""
    logger.info(f"Validating CSV: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"CSV file not found: {file_path}")
        return False
    
    if os.path.getsize(file_path) == 0:
        logger.error(f"CSV file is empty: {file_path}")
        return False
    
    try:
        schema = load_schema(schema_path)
        # Read CSV data
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            logger.error(f"CSV file has no data rows: {file_path}")
            return False
        
        # Validate against schema (simplified check for required columns)
        required_columns = schema.get('required_columns', [])
        if required_columns:
            first_row_keys = set(rows[0].keys())
            missing_cols = set(required_columns) - first_row_keys
            if missing_cols:
                logger.error(f"CSV missing required columns: {missing_cols}")
                return False
        
        # Validate specific data types for key columns
        for row in rows:
            if 'consistency_score' in row:
                try:
                    score = float(row['consistency_score'])
                    if not (-1.0 <= score <= 1.0):
                        logger.error(f"Consistency score out of range: {score}")
                        return False
                except ValueError:
                    logger.error(f"Invalid consistency score format: {row['consistency_score']}")
                    return False
            
            if 'trust_score' in row:
                try:
                    score = float(row['trust_score'])
                    if score < 0 or score > 100:
                        logger.error(f"Trust score out of range: {score}")
                        return False
                except ValueError:
                    logger.error(f"Invalid trust score format: {row['trust_score']}")
                    return False
        
        logger.info(f"CSV validation passed: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"CSV validation failed: {str(e)}")
        return False

def validate_json_schema(file_path: str, schema_path: str) -> bool:
    """Validate JSON file against feature extraction schema."""
    logger.info(f"Validating JSON: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"JSON file not found: {file_path}")
        return False
    
    if os.path.getsize(file_path) == 0:
        logger.error(f"JSON file is empty: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        schema = load_schema(schema_path)
        
        # Check for required top-level keys
        required_keys = schema.get('required_keys', [])
        if required_keys:
            missing_keys = set(required_keys) - set(data.keys())
            if missing_keys:
                logger.error(f"JSON missing required keys: {missing_keys}")
                return False
        
        # Validate correlation coefficient
        if 'correlation_coefficient' in data:
            corr = float(data['correlation_coefficient'])
            if not (-1.0 <= corr <= 1.0):
                logger.error(f"Correlation coefficient out of range: {corr}")
                return False
        
        # Validate confidence interval
        if 'confidence_interval' in data:
            ci = data['confidence_interval']
            if not isinstance(ci, list) or len(ci) != 2:
                logger.error("Confidence interval must be a list of two values")
                return False
            if ci[0] > ci[1]:
                logger.error("Confidence interval lower bound > upper bound")
                return False
        
        logger.info(f"JSON validation passed: {file_path}")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"JSON validation failed: {str(e)}")
        return False

def validate_png_file(file_path: str) -> bool:
    """Validate PNG file for existence, non-zero size, and valid header."""
    logger.info(f"Validating PNG: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"PNG file not found: {file_path}")
        return False
    
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        logger.error(f"PNG file is empty: {file_path}")
        return False
    
    if file_size < 8:
        logger.error(f"PNG file too small to be valid: {file_path}")
        return False
    
    # Check PNG signature (first 8 bytes)
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    expected_signature = b'\x89PNG\r\n\x1a\n'
    
    try:
        with open(file_path, 'rb') as f:
            signature = f.read(8)
            if signature != expected_signature:
                logger.error(f"Invalid PNG signature: {signature.hex()}")
                return False
    except Exception as e:
        logger.error(f"Error reading PNG file: {str(e)}")
        return False
    
    # Additional check: try to parse IHDR chunk (basic validation)
    try:
        with open(file_path, 'rb') as f:
            f.read(8)  # Skip signature
            # Read length (4 bytes, big-endian)
            length_bytes = f.read(4)
            if len(length_bytes) < 4:
                logger.error("PNG file truncated before IHDR length")
                return False
            length = struct.unpack('>I', length_bytes)[0]
            
            # Read chunk type (4 bytes)
            chunk_type = f.read(4)
            if chunk_type != b'IHDR':
                logger.error(f"Expected IHDR chunk, got: {chunk_type}")
                return False
            
            # Read IHDR data (13 bytes)
            ihdr_data = f.read(13)
            if len(ihdr_data) < 13:
                logger.error("PNG file truncated in IHDR data")
                return False
            
            # Parse width and height (first 8 bytes of IHDR data)
            width = struct.unpack('>I', ihdr_data[0:4])[0]
            height = struct.unpack('>I', ihdr_data[4:8])[0]
            
            if width == 0 or height == 0:
                logger.error(f"PNG has zero dimensions: {width}x{height}")
                return False
            
            logger.info(f"PNG validation passed: {file_path} ({width}x{height})")
            return True
            
    except Exception as e:
        logger.error(f"Error parsing PNG structure: {str(e)}")
        return False

def validate_success_criteria() -> Tuple[bool, List[str]]:
    """
    Validate all success criteria for T028:
    1. CSV exists and matches schema
    2. JSON exists and matches schema
    3. PNG exists and is valid
    4. All required columns present in CSV
    5. Correlation coefficient and CI present in JSON
    6. PNG has non-zero dimensions
    """
    all_valid = True
    failures = []
    
    # Validate CSV
    csv_valid = validate_csv_schema(OUTPUT_CSV_PATH, SCHEMA_PATH_DATASET)
    if not csv_valid:
        all_valid = False
        failures.append("CSV validation failed")
    else:
        # Additional CSV checks
        with open(OUTPUT_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if len(rows) < 1:
            all_valid = False
            failures.append("CSV has no data rows")
        else:
            # Check for required columns
            required_cols = ['interaction_id', 'consistency_score', 'trust_score']
            missing_cols = [col for col in required_cols if col not in rows[0]]
            if missing_cols:
                all_valid = False
                failures.append(f"CSV missing columns: {missing_cols}")
    
    # Validate JSON
    json_valid = validate_json_schema(OUTPUT_JSON_PATH, SCHEMA_PATH_FEATURES)
    if not json_valid:
        all_valid = False
        failures.append("JSON validation failed")
    else:
        # Additional JSON checks
        with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'correlation_coefficient' not in data:
            all_valid = False
            failures.append("JSON missing correlation_coefficient")
        if 'confidence_interval' not in data:
            all_valid = False
            failures.append("JSON missing confidence_interval")
        if 'p_value' not in data:
            all_valid = False
            failures.append("JSON missing p_value")
    
    # Validate PNG
    png_valid = validate_png_file(OUTPUT_PNG_PATH)
    if not png_valid:
        all_valid = False
        failures.append("PNG validation failed")
    
    return all_valid, failures

def main():
    """Main entry point for T028 validation."""
    logger.info("=" * 60)
    logger.info("Starting T028: Output Artifact Validation")
    logger.info("=" * 60)
    
    logger.info(f"Checking paths:")
    logger.info(f"  CSV: {OUTPUT_CSV_PATH}")
    logger.info(f"  JSON: {OUTPUT_JSON_PATH}")
    logger.info(f"  PNG: {OUTPUT_PNG_PATH}")
    
    all_valid, failures = validate_success_criteria()
    
    if all_valid:
        logger.info("=" * 60)
        logger.info("SUCCESS: All output artifacts validated successfully")
        logger.info("=" * 60)
        print("VALIDATION_PASSED")
        return 0
    else:
        logger.error("=" * 60)
        logger.error("FAILURE: Output validation failed")
        for failure in failures:
            logger.error(f"  - {failure}")
        logger.error("=" * 60)
        print("VALIDATION_FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
