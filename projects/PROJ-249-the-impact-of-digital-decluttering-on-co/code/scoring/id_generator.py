"""
Pseudonymous ID Generator for Digital Decluttering Study.

Implements FR-001: Generates participant IDs adhering to the pattern P\d{3}
(e.g., P001, P002, ..., P999).

Supports deterministic ID generation from:
1. A recruitment CSV file (reading existing IDs or assigning new ones)
2. A synthetic source (generating a sequence of IDs for simulation)

Ensures deterministic linking of baseline/post data by maintaining a mapping
or generating IDs in a reproducible order.
"""
import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Optional, Union, Iterator
import numpy as np

from utils.random_seed import get_rng, set_global_seed

# Regex pattern for valid IDs: P followed by exactly 3 digits
ID_PATTERN = re.compile(r'^P\d{3}$')
MAX_ID_VALUE = 999

def validate_id_format(participant_id: str) -> bool:
    """
    Validates that a participant ID matches the required P\d{3} pattern.

    Args:
        participant_id: The ID string to validate.

    Returns:
        True if valid, False otherwise.
    """
    return bool(ID_PATTERN.match(participant_id))

def parse_id_suffix(participant_id: str) -> int:
    """
    Extracts the numeric suffix from a valid P\d{3} ID.

    Args:
        participant_id: The ID string (e.g., 'P042').

    Returns:
        The integer suffix (e.g., 42).

    Raises:
        ValueError: If the ID format is invalid.
    """
    if not validate_id_format(participant_id):
        raise ValueError(f"Invalid ID format: {participant_id}. Must match P\\d{{3}}.")
    return int(participant_id[1:])

def generate_sequence_ids(start: int = 1, count: int = 1, seed: Optional[int] = None) -> List[str]:
    """
    Generates a deterministic sequence of P\d{3} IDs.

    Args:
        start: The starting integer suffix (1-999). Defaults to 1.
        count: The number of IDs to generate.
        seed: Optional random seed for reproducibility if shuffling is needed later,
              though this function generates a strict sequence.

    Returns:
        A list of valid P\d{3} strings.

    Raises:
        ValueError: If start + count exceeds 999.
    """
    if start < 1 or start > MAX_ID_VALUE:
        raise ValueError(f"Start index must be between 1 and {MAX_ID_VALUE}.")
    if start + count - 1 > MAX_ID_VALUE:
        raise ValueError(f"Cannot generate {count} IDs starting from {start}. Max ID is P{MAX_ID_VALUE}.")

    ids = [f"P{i:03d}" for i in range(start, start + count)]
    return ids

def load_ids_from_csv(csv_path: Union[str, Path], id_column: Optional[str] = None) -> List[str]:
    """
    Loads existing participant IDs from a recruitment CSV file.

    If `id_column` is provided, it reads from that column. Otherwise, it assumes
    the first column contains IDs or scans for a column named 'participant_id'.

    Args:
        csv_path: Path to the recruitment CSV.
        id_column: Optional name of the column containing IDs.

    Returns:
        A list of valid P\d{3} IDs found in the file.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If no valid IDs are found or the format is incorrect.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Recruitment CSV not found: {csv_path}")

    ids = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Determine the ID column
        if id_column:
            target_col = id_column
        else:
            # Try common names, then fallback to first column
            possible_cols = ['participant_id', 'id', 'pid', 'subject_id']
            if reader.fieldnames:
                found = next((col for col in possible_cols if col in reader.fieldnames), None)
                if not found and len(reader.fieldnames) > 0:
                    found = reader.fieldnames[0]
                if not found:
                    raise ValueError("Could not determine ID column. Please specify 'id_column'.")
                target_col = found
            else:
                raise ValueError("CSV file appears to be empty or missing headers.")

        for row in reader:
            raw_id = row.get(target_col, "").strip()
            if not raw_id:
                continue
            
            if not validate_id_format(raw_id):
                # Log warning or skip? For strictness, we raise or skip invalid ones.
                # Given the requirement for deterministic linking, we should probably fail
                # if the source data is malformed, or just skip and warn.
                # Let's skip invalid ones to be robust, but ensure we have at least some.
                continue
            
            ids.append(raw_id)

    if not ids:
        raise ValueError(f"No valid P\\d{{3}} IDs found in {csv_path} under column '{target_col}'.")
    
    return ids

def get_next_available_id(existing_ids: List[str], start: int = 1) -> str:
    """
    Finds the next available ID in the sequence P\d{3} that is not in `existing_ids`.

    Args:
        existing_ids: List of IDs already in use.
        start: The starting index to search from.

    Returns:
        The next available ID string.
    """
    used_suffixes = set()
    for pid in existing_ids:
        if validate_id_format(pid):
            used_suffixes.add(parse_id_suffix(pid))
    
    current = start
    while current <= MAX_ID_VALUE:
        if current not in used_suffixes:
            return f"P{current:03d}"
        current += 1
    
    raise RuntimeError("All possible P\\d{{3}} IDs are exhausted.")

class IDGenerator:
    """
    A generator class to manage pseudonymous ID assignment for the study.
    Ensures deterministic linking and adherence to FR-001.
    """
    def __init__(self, seed: Optional[int] = None):
        """
        Initializes the ID generator.

        Args:
            seed: Optional seed for reproducibility if randomization is introduced later.
        """
        self.seed = seed
        if seed is not None:
            set_global_seed(seed)
        self._used_ids: set = set()
        self._rng = get_rng()

    def add_existing_ids(self, ids: List[str]) -> None:
        """
        Registers existing IDs to prevent duplication.

        Args:
            ids: List of existing P\d{3} IDs.
        """
        for pid in ids:
            if not validate_id_format(pid):
                raise ValueError(f"Invalid ID provided: {pid}")
            self._used_ids.add(pid)

    def load_from_csv(self, csv_path: Union[str, Path], id_column: Optional[str] = None) -> int:
        """
        Loads existing IDs from a CSV file to initialize the generator.

        Args:
            csv_path: Path to the CSV.
            id_column: Optional column name.

        Returns:
            The number of IDs loaded.
        """
        ids = load_ids_from_csv(csv_path, id_column)
        self.add_existing_ids(ids)
        return len(ids)

    def generate(self, count: int = 1) -> List[str]:
        """
        Generates new unique IDs.

        Args:
            count: Number of IDs to generate.

        Returns:
            List of new unique P\d{3} IDs.
        """
        if len(self._used_ids) + count > MAX_ID_VALUE:
            raise RuntimeError(f"Cannot generate {count} more IDs. Only {MAX_ID_VALUE - len(self._used_ids)} remaining.")
        
        new_ids = []
        current = 1
        while len(new_ids) < count:
            candidate = f"P{current:03d}"
            if candidate not in self._used_ids:
                new_ids.append(candidate)
                self._used_ids.add(candidate)
            current += 1
            if current > MAX_ID_VALUE:
                break # Should be caught by the length check, but safe guard
        
        return new_ids

    def reset(self) -> None:
        """Resets the generator state."""
        self._used_ids.clear()

def main():
    """
    Command-line entry point for testing the ID generator.
    Demonstrates generating IDs from a synthetic source and validating format.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Pseudonymous ID Generator for Digital Decluttering Study")
    parser.add_argument("--mode", choices=["sequence", "csv", "next"], default="sequence",
                        help="Mode of operation: generate sequence, load from CSV, or find next available.")
    parser.add_argument("--count", type=int, default=5, help="Number of IDs to generate (for sequence mode).")
    parser.add_argument("--start", type=int, default=1, help="Starting index (for sequence mode).")
    parser.add_argument("--csv-path", type=str, help="Path to recruitment CSV (for csv/next mode).")
    parser.add_argument("--id-column", type=str, help="Column name in CSV containing IDs.")
    parser.add_argument("--output", type=str, help="Optional output file path (CSV).")
    
    args = parser.parse_args()

    generator = IDGenerator(seed=42) # Fixed seed for reproducibility in examples

    if args.mode == "sequence":
        ids = generate_sequence_ids(start=args.start, count=args.count)
        print(f"Generated {len(ids)} sequence IDs:")
        for pid in ids:
            print(f"  {pid}")
        
        if args.output:
            with open(args.output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['participant_id'])
                for pid in ids:
                    writer.writerow([pid])
            print(f"Written to {args.output}")

    elif args.mode == "csv":
        if not args.csv_path:
            parser.error("--csv-path is required for csv mode.")
        try:
            ids = load_ids_from_csv(args.csv_path, args.id_column)
            print(f"Loaded {len(ids)} valid IDs from {args.csv_path}")
            print(f"First 5: {ids[:5]}")
            
            # Validate all
            all_valid = all(validate_id_format(pid) for pid in ids)
            print(f"All IDs valid (P\\d{{3}}): {all_valid}")
        except Exception as e:
            print(f"Error loading CSV: {e}")

    elif args.mode == "next":
        if not args.csv_path:
            parser.error("--csv-path is required for next mode.")
        try:
            existing = load_ids_from_csv(args.csv_path, args.id_column)
            next_id = get_next_available_id(existing)
            print(f"Next available ID: {next_id}")
        except Exception as e:
            print(f"Error finding next ID: {e}")

if __name__ == "__main__":
    main()
