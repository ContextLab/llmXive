"""
Data preprocessing module for the GateMem dataset.

This module provides functions to clean, format, and normalize the GateMem dataset
for downstream processing by the Gatekeeper pipeline. It depends on the data loader
module (T004) to fetch and validate the raw data.

Dependencies:
    - code/data/loader.py (fetch_gatemem, validate_fields, inject_fallback_data)
"""
import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from datasets import Dataset

# Ensure we can import from sibling module
from code.data.loader import fetch_gatemem, validate_fields, inject_fallback_data


def clean_text(text: str) -> str:
    """
    Clean and normalize raw text fields.
    
    Args:
        text: Raw text string to clean.
        
    Returns:
        Cleaned text string.
    """
    if not isinstance(text, str):
        return ""
    
    # Remove excessive whitespace and normalize newlines
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Remove common artifacts (HTML tags, special characters)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def clean_and_format(dataset_path: str, output_path: str) -> Dict[str, Any]:
    """
    Preprocess the GateMem dataset: clean text fields, format structures,
    and save to a processed dataset file.
    
    This function:
    1. Loads the validated dataset from the raw/processed location
    2. Applies text cleaning to relevant fields
    3. Ensures consistent formatting of metadata fields
    4. Saves the cleaned dataset to the specified output path
    
    Args:
        dataset_path: Path to the validated dataset file (JSON/Parquet/CSV).
                      Expected in data/raw/ or data/processed/ from previous steps.
        output_path: Path where the cleaned dataset will be saved.
                      Must end in .json or .csv.
                      
    Returns:
        Dict containing processing statistics:
            - rows_processed: int
            - rows_cleaned: int
            - output_path: str
            - fields_processed: List[str]
            
    Raises:
        FileNotFoundError: If input dataset_path does not exist.
        ValueError: If output_path format is unsupported.
    """
    # Ensure input file exists
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Input dataset not found: {dataset_path}")
    
    # Determine file format and load
    _, ext = os.path.splitext(dataset_path)
    ext = ext.lower()
    
    if ext == '.json':
        df = pd.read_json(dataset_path, orient='records')
    elif ext == '.csv':
        df = pd.read_csv(dataset_path)
    elif ext == '.parquet':
        df = pd.read_parquet(dataset_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .json, .csv, or .parquet")
    
    if df.empty:
        raise ValueError("Dataset is empty after loading.")
    
    # Define fields to clean (text-based fields)
    text_fields = ['query', 'context', 'memory', 'response', 'leak-target', 'role']
    cleaned_fields = []
    
    # Track statistics
    rows_processed = len(df)
    rows_cleaned = 0
    
    for field in text_fields:
        if field in df.columns:
            cleaned_fields.append(field)
            # Apply cleaning function
            df[field] = df[field].apply(clean_text)
            rows_cleaned += len(df)
    
    # Ensure required fields exist (fallback to empty string if missing)
    required_fields = ['query', 'role']
    for field in required_fields:
        if field not in df.columns:
            df[field] = ""
    
    # Format metadata fields (ensure consistent types)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    if 'leak-target' in df.columns:
        # Ensure leak-target is string (handle NaN)
        df['leak-target'] = df['leak-target'].fillna('').astype(str)
    
    # Save to output path
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    if output_path.endswith('.json'):
        df.to_json(output_path, orient='records', lines=False, force_ascii=False)
    elif output_path.endswith('.csv'):
        df.to_csv(output_path, index=False)
    elif output_path.endswith('.parquet'):
        df.to_parquet(output_path, index=False)
    
    return {
        "rows_processed": rows_processed,
        "rows_cleaned": rows_cleaned,
        "output_path": output_path,
        "fields_processed": cleaned_fields
    }


def run_preprocessing_pipeline() -> str:
    """
    Execute the full preprocessing pipeline:
    1. Fetch raw data (if not already present)
    2. Validate fields
    3. Inject fallback data if needed
    4. Clean and format
    5. Save to processed directory
    
    Returns:
        Path to the final processed dataset file.
    """
    # Define paths
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # Step 1: Fetch raw data (T004)
    raw_file = fetch_gatemem()
    
    # Step 2 & 3: Validate and inject fallback (T004a, T004c)
    validated_file = inject_fallback_data(raw_file)
    
    # Step 4 & 5: Clean and format
    output_file = os.path.join(processed_dir, "gatemem_cleaned.json")
    stats = clean_and_format(validated_file, output_file)
    
    # Log stats
    print(f"Preprocessing complete: {stats['rows_processed']} rows processed")
    print(f"Output saved to: {output_file}")
    
    return output_file


if __name__ == "__main__":
    # Run the pipeline when executed directly
    output_path = run_preprocessing_pipeline()
    print(f"Final dataset: {output_path}")
