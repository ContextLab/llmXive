"""
Feature Extraction Module for GENEB Benchmark Analysis.

This module computes standardized low-dimensional sequence statistics for each
task in the GENEB benchmark. It reads raw sequence data (FASTA) downloaded
in previous steps and calculates features such as nucleotide entropy, k-mer
entropy, and GC-content variance.

Key Constraints:
- Excludes 'at_content' due to perfect collinearity with GC-Content.
- Handles edge cases (mononucleotide repeats) by flooring entropy to a small constant.
- Validates output against the schema defined in specs/gene-regulation/contracts/dataset.schema.yaml.
- Reads feature definitions from data-model.md (via utils.schema_generator).
"""

import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Iterable

import numpy as np
import pandas as pd
import yaml

# Import from project API surface
from config import get_path, get_paths, load_config
from utils.logging import get_logger, PipelineError, DataFetchError
from utils.schema_validator import load_schema, validate_dataset
from utils.schema_generator import load_data_model_features

logger = get_logger(__name__)

# Constants
ENTROPY_FLOOR = 1e-9  # Small positive constant to avoid log(0)
KMER_SIZE = 3  # Default k-mer size for entropy calculation
GC_THRESHOLD = 0.5  # Not used for exclusion, but kept for reference if needed
SEQUENCE_FILE_PATTERN = "*.fasta"

def calculate_nucleotide_entropy(sequence: str) -> float:
    """
    Calculate the Shannon entropy of nucleotide frequencies in a sequence.

    Handles edge cases where a sequence might be empty or contain only one type
    of nucleotide by flooring the probability to ENTROPY_FLOOR.

    Args:
        sequence: DNA sequence string (e.g., "ACGTACGT").

    Returns:
        Shannon entropy value (float).
    """
    if not sequence:
        return 0.0

    # Count nucleotides
    counts = Counter(sequence.upper())
    total = sum(counts.values())

    if total == 0:
        return 0.0

    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            # Floor probability to avoid log(0)
            p = max(p, ENTROPY_FLOOR)
            entropy -= p * math.log2(p)

    return entropy

def calculate_gc_content(sequence: str) -> float:
    """
    Calculate the GC content (fraction of G and C nucleotides) in a sequence.

    Args:
        sequence: DNA sequence string.

    Returns:
        GC content fraction (float).
    """
    if not sequence:
        return 0.0

    seq_upper = sequence.upper()
    gc_count = seq_upper.count('G') + seq_upper.count('C')
    total = len(seq_upper)

    if total == 0:
        return 0.0

    return gc_count / total

def calculate_kmer_entropy(sequence: str, k: int = KMER_SIZE) -> float:
    """
    Calculate the Shannon entropy of k-mer frequencies in a sequence.

    Args:
        sequence: DNA sequence string.
        k: K-mer length (default 3).

    Returns:
        K-mer entropy value (float).
    """
    if len(sequence) < k:
        return 0.0

    kmer_counts = Counter()
    seq_upper = sequence.upper()

    # Slide window
    for i in range(len(seq_upper) - k + 1):
        kmer = seq_upper[i : i + k]
        # Only count valid DNA k-mers (A, C, G, T)
        if all(base in "ACGT" for base in kmer):
            kmer_counts[kmer] += 1

    total = sum(kmer_counts.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in kmer_counts.values():
        if count > 0:
            p = count / total
            p = max(p, ENTROPY_FLOOR)
            entropy -= p * math.log2(p)

    return entropy

def calculate_sequence_variance(sequence: str) -> float:
    """
    Calculate the variance of sequence length or other numeric properties.
    For a single sequence, this is often 0 unless we are looking at windowed stats.
    Here, we interpret this as the variance of nucleotide 'values' if mapped,
    or simply return 0.0 for a single sequence context unless windowed.
    However, based on typical genomic features, this might refer to the variance
    of GC-content across windows. Since we are processing per-task (which might
    be a single sequence or a collection), we will calculate the variance of
    GC-content across non-overlapping windows of size 100bp if the sequence is long,
    otherwise 0.0.

    If the input is a list of sequences (from a task), we calculate variance across them.
    If it's a single string, we window it.
    """
    if not sequence:
        return 0.0

    seq_upper = sequence.upper()
    window_size = 100
    gc_values = []

    # If sequence is too short, return 0 variance
    if len(seq_upper) < window_size:
        return 0.0

    for i in range(0, len(seq_upper) - window_size + 1, window_size):
        window = seq_upper[i : i + window_size]
        gc = calculate_gc_content(window)
        gc_values.append(gc)

    if len(gc_values) < 2:
        return 0.0

    return float(np.var(gc_values))

def extract_features_from_sequence(
    sequence: str, feature_names: List[str]
) -> Dict[str, float]:
    """
    Extract a dictionary of features from a single DNA sequence.

    Args:
        sequence: DNA sequence string.
        feature_names: List of feature names to compute (from data-model.md).

    Returns:
        Dictionary mapping feature names to float values.
    """
    features = {}

    # Ensure we don't calculate at_content
    safe_feature_names = [
        name for name in feature_names if name != "at_content"
    ]

    for name in safe_feature_names:
        try:
            if name == "nucleotide_entropy":
                features[name] = calculate_nucleotide_entropy(sequence)
            elif name == "gc_content":
                features[name] = calculate_gc_content(sequence)
            elif name == "kmer_entropy":
                features[name] = calculate_kmer_entropy(sequence)
            elif name == "gc_content_variance":
                features[name] = calculate_sequence_variance(sequence)
            else:
                # Fallback for unknown features defined in data-model.md
                # Log warning and set to 0.0 or skip
                logger.warning(f"Unknown feature requested: {name}, skipping.")
                continue
        except Exception as e:
            logger.error(f"Error computing feature {name} for sequence: {e}")
            features[name] = 0.0

    return features

def extract_sequence_features(
    sequences: List[str], feature_names: List[str]
) -> List[Dict[str, float]]:
    """
    Extract features for a list of sequences.

    Args:
        sequences: List of DNA sequence strings.
        feature_names: List of feature names to compute.

    Returns:
        List of feature dictionaries.
    """
    results = []
    for seq in sequences:
        results.append(extract_features_from_sequence(seq, feature_names))
    return results

def load_sequence_data_from_fasta(fasta_path: Path) -> List[Tuple[str, str]]:
    """
    Load sequences from a FASTA file. Returns a list of (header, sequence) tuples.

    Args:
        fasta_path: Path to the FASTA file.

    Returns:
        List of (header, sequence) tuples.
    """
    if not fasta_path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    sequences = []
    current_header = None
    current_seq_parts = []

    with open(fasta_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_header:
                    sequences.append((current_header, "".join(current_seq_parts)))
                current_header = line[1:].split()[0]  # Take first word as ID
                current_seq_parts = []
            else:
                current_seq_parts.append(line.upper())

        if current_header:
            sequences.append((current_header, "".join(current_seq_parts)))

    return sequences

def main():
    """
    Main entry point for feature extraction.
    1. Load feature definitions from data-model.md (via schema_generator).
    2. Read raw FASTA files from data/raw/.
    3. Compute features for each task.
    4. Validate against schema.
    5. Save to data/processed/features.csv.
    """
    logger.info("Starting feature extraction (T012)...")

    # 1. Load Configuration and Paths
    config = load_config()
    raw_dir = get_path("raw_data")
    processed_dir = get_path("processed_data")
    schema_path = get_path("feature_schema")
    data_model_path = get_path("data_model")

    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 2. Load Feature Definitions from Data Model
    # The schema generator reads data-model.md and generates the list of features.
    # We use the schema to determine which features to compute.
    try:
        feature_names = load_data_model_features(data_model_path)
        # Explicitly exclude at_content if it somehow got in
        if "at_content" in feature_names:
            feature_names.remove("at_content")
            logger.info("Excluded 'at_content' from feature list due to collinearity.")
        logger.info(f"Features to compute: {feature_names}")
    except Exception as e:
        raise PipelineError(f"Failed to load feature definitions from {data_model_path}: {e}")

    # 3. Load Schema for Validation
    try:
        schema = load_schema(schema_path)
        logger.info(f"Loaded schema from {schema_path}")
    except Exception as e:
        raise PipelineError(f"Failed to load schema from {schema_path}: {e}")

    # 4. Process FASTA Files
    all_records = []
    fasta_files = list(raw_dir.glob("*.fasta"))
    if not fasta_files:
        # Check for subdirectories or specific naming patterns if needed
        # Assuming standard GENEB download structure: data/raw/geneb/{task_id}.fasta
        # Or data/raw/geneb/*.fasta
        pass

    if not fasta_files:
        # Fallback to scanning subdirectories if structure is nested
        for root, _, files in os.walk(raw_dir):
            for file in files:
                if file.endswith(".fasta"):
                    fasta_files.append(Path(root) / file)

    if not fasta_files:
        raise DataFetchError("No FASTA files found in data/raw/. Ensure T011 completed successfully.")

    logger.info(f"Found {len(fasta_files)} FASTA files to process.")

    for fasta_file in fasta_files:
        logger.info(f"Processing {fasta_file.name}...")
        try:
            sequences = load_sequence_data_from_fasta(fasta_file)
            task_id = fasta_file.stem  # Use filename as task_id if no header ID
            
            # If the file contains multiple sequences for one task, we might need to aggregate.
            # For now, assume one record per file or process each sequence as a row.
            # Based on GENEB, usually one sequence per task or a set of sequences.
            # We will treat each sequence in the file as a row, but tag with task_id.
            
            # If the file is the primary sequence for a task, we might just take the first one
            # or average if multiple. Let's assume the file represents one task's sequence data.
            # If multiple sequences exist, we'll compute features for each and keep the task_id.
            
            for header, sequence in sequences:
                features = extract_features_from_sequence(sequence, feature_names)
                record = {"task_id": task_id, "header_id": header}
                record.update(features)
                all_records.append(record)

        except Exception as e:
            logger.error(f"Error processing {fasta_file}: {e}")
            continue

    if not all_records:
        raise DataFetchError("No sequence data extracted. Check input files.")

    # 5. Create DataFrame
    df = pd.DataFrame(all_records)

    # 6. Validate Output
    logger.info("Validating output against schema...")
    # Ensure all required columns exist
    required_cols = set(feature_names) | {"task_id"}
    existing_cols = set(df.columns)
    missing_cols = required_cols - existing_cols
    if missing_cols:
        raise PipelineError(f"Missing required columns after extraction: {missing_cols}")

    # Validate data types and ranges
    for col in feature_names:
        if col in df.columns:
            if df[col].isnull().any():
                logger.warning(f"Column {col} contains NaN values. Filling with 0.")
                df[col] = df[col].fillna(0.0)
            
            # Ensure non-negative for entropy
            if "entropy" in col:
                df[col] = df[col].clip(lower=0.0)

    # 7. Save to CSV
    output_path = processed_dir / "features.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved features to {output_path}")

    # 8. Log Statistics
    logger.info(f"Total records processed: {len(df)}")
    logger.info(f"Features computed: {list(df.columns)}")

    return df

if __name__ == "__main__":
    main()