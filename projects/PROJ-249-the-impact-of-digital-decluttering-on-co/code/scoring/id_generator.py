"""
ID Generator Module for Pseudonymous Participant Identification.

This module implements the generation and validation of pseudonymous IDs
adhering to the FR-001 requirement: pattern `P\d{3}` (e.g., P001, P099).

It ensures deterministic linking of baseline and post-intervention data
by generating IDs from a recruitment CSV or an existing registry.
"""
import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Optional, Union, Iterator
import numpy as np

# Constants
ID_PATTERN = r'^P\d{3}$'
DEFAULT_ID_PREFIX = 'P'
DEFAULT_ID_LENGTH = 3  # Total length including prefix 'P' + 3 digits
MAX_ID_VALUE = 999

def validate_id_format(participant_id: str) -> bool:
    """
    Validates if a given ID matches the required pattern P\d{3}.

    Args:
        participant_id: The ID string to validate.

    Returns:
        True if the ID matches the pattern, False otherwise.
    """
    if not isinstance(participant_id, str):
        return False
    return bool(re.match(ID_PATTERN, participant_id))


def parse_id_suffix(participant_id: str) -> Optional[int]:
    """
    Extracts the numeric suffix from a P\d{3} ID.

    Args:
        participant_id: The ID string (e.g., 'P042').

    Returns:
        The integer suffix (e.g., 42), or None if invalid.
    """
    if not validate_id_format(participant_id):
        return None
    return int(participant_id[1:])


def generate_sequence_ids(start: int = 1, count: int = 100) -> Iterator[str]:
    """
    Generates a sequence of pseudonymous IDs starting from a given index.

    Args:
        start: The starting numeric index (inclusive).
        count: The number of IDs to generate.

    Yields:
        Strings formatted as 'P001', 'P002', etc.

    Raises:
        ValueError: If the sequence exceeds the maximum allowed ID (P999).
    """
    if start < 1:
        raise ValueError("Start index must be >= 1")
    
    current = start
    for _ in range(count):
        if current > MAX_ID_VALUE:
            raise ValueError(f"Exceeded maximum ID limit ({MAX_ID_VALUE}). Cannot generate more IDs.")
        yield f"{DEFAULT_ID_PREFIX}{current:03d}"
        current += 1


def load_ids_from_csv(csv_path: Union[str, Path]) -> List[str]:
    """
    Loads existing participant IDs from a CSV file.

    Expects the CSV to have a column named 'participant_id'.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        List of existing participant ID strings.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        KeyError: If 'participant_id' column is missing.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")
    
    ids = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'participant_id' not in reader.fieldnames:
            raise KeyError(f"CSV must contain 'participant_id' column. Found: {reader.fieldnames}")
        
        for row in reader:
            pid = row['participant_id'].strip()
            if pid:
                if not validate_id_format(pid):
                    raise ValueError(f"Invalid ID format in registry: {pid}")
                ids.append(pid)
    return ids


def get_next_available_id(existing_ids: List[str], start: int = 1) -> str:
    """
    Finds the next available ID starting from 'start' that is not in 'existing_ids'.

    Args:
        existing_ids: List of currently used IDs.
        start: Starting index to search from.

    Returns:
        The next available ID string.

    Raises:
        ValueError: If no ID is available up to P999.
    """
    existing_set = set(existing_ids)
    current = start
    while current <= MAX_ID_VALUE:
        candidate = f"{DEFAULT_ID_PREFIX}{current:03d}"
        if candidate not in existing_set:
            return candidate
        current += 1
    raise ValueError(f"No available IDs found between P{start:03d} and P{MAX_ID_VALUE}.")


class IDGenerator:
    """
    A class to manage the generation of pseudonymous IDs for participants.
    It handles state (used IDs) and ensures uniqueness and format compliance.
    """
    
    def __init__(self, registry_path: Optional[Union[str, Path]] = None):
        """
        Initializes the IDGenerator.

        Args:
            registry_path: Optional path to an existing registry CSV to load used IDs from.
        """
        self.used_ids: set = set()
        self.next_index: int = 1
        self.registry_path = Path(registry_path) if registry_path else None

        if self.registry_path and self.registry_path.exists():
            self._load_registry()
        
        # Determine the next index based on the highest existing ID
        if self.used_ids:
            max_suffix = max(parse_id_suffix(pid) for pid in self.used_ids if parse_id_suffix(pid))
            self.next_index = max_suffix + 1

    def _load_registry(self):
        """Loads existing IDs from the registry file."""
        try:
            loaded_ids = load_ids_from_csv(self.registry_path)
            self.used_ids.update(loaded_ids)
        except FileNotFoundError:
            # If registry doesn't exist yet, start fresh
            pass
        except (KeyError, ValueError) as e:
            # Log error but allow initialization to proceed (or fail loudly depending on strictness)
            # For this implementation, we raise to ensure data integrity
            raise RuntimeError(f"Failed to load registry due to data integrity error: {e}")

    def generate(self, count: int = 1) -> List[str]:
        """
        Generates a specified number of new unique IDs.

        Args:
            count: Number of IDs to generate.

        Returns:
            List of generated ID strings.

        Raises:
            ValueError: If unable to generate the requested number of IDs.
        """
        generated = []
        for _ in range(count):
            try:
                new_id = get_next_available_id(list(self.used_ids), self.next_index)
                self.used_ids.add(new_id)
                # Update next_index to be one past the generated ID
                self.next_index = parse_id_suffix(new_id) + 1
                generated.append(new_id)
            except ValueError as e:
                raise ValueError(f"Could not generate {count} IDs. Reason: {e}")
        return generated

    def save_registry(self, output_path: Union[str, Path]):
        """
        Saves the current state of used IDs to a CSV file.

        Args:
            output_path: Path to save the registry CSV.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['participant_id'])
            writer.writeheader()
            for pid in sorted(self.used_ids):
                writer.writerow({'participant_id': pid})

    def get_stats(self) -> Dict[str, int]:
        """Returns statistics about the current ID usage."""
        return {
            'total_generated': len(self.used_ids),
            'next_available_index': self.next_index,
            'max_possible': MAX_ID_VALUE
        }

def main():
    """
    Main entry point for testing the ID generator module.
    Demonstrates generation, validation, and registry saving.
    """
    import sys
    
    # Example usage
    print("Initializing ID Generator...")
    generator = IDGenerator()
    
    # Generate 5 IDs
    new_ids = generator.generate(5)
    print(f"Generated IDs: {new_ids}")
    
    # Validate them
    for pid in new_ids:
        assert validate_id_format(pid), f"Invalid format: {pid}"
    
    # Save to a temporary registry for demonstration
    output_path = "data/raw/test_registry.csv"
    generator.save_registry(output_path)
    print(f"Registry saved to {output_path}")
    
    # Load and verify
    loaded = load_ids_from_csv(output_path)
    assert set(loaded) == set(new_ids), "Loaded IDs do not match generated IDs"
    print("Verification successful.")

if __name__ == "__main__":
    main()