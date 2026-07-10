"""
Low-complexity filtering utility for genomic sequences.

Implements Shannon entropy-based filtering to exclude repetitive regions
from analysis. Regions with entropy below a threshold (default > 0.8)
are considered low-complexity and excluded.

This utility is a prerequisite for US1 data ingestion (T012-T017) to ensure
that repetitive genomic regions do not bias the CTCF binding predictions.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Default threshold for Shannon entropy (higher = less repetitive)
DEFAULT_ENTROPY_THRESHOLD = 0.8

def calculate_shannon_entropy(sequence: str) -> float:
    """
    Calculate the Shannon entropy of a DNA sequence.

    The entropy is calculated based on the frequency of each nucleotide (A, C, G, T).
    Nucleotides are case-insensitive. Non-standard characters are ignored.

    Args:
        sequence: DNA sequence string (e.g., "ACGTACGT")

    Returns:
        Shannon entropy value between 0 (completely repetitive) and 2 (maximally diverse for 4 bases)
    """
    if not sequence:
        return 0.0

    # Count nucleotide frequencies
    counts = {'A': 0, 'C': 0, 'G': 0, 'T': 0}
    total = 0

    for char in sequence.upper():
        if char in counts:
            counts[char] += 1
            total += 1

    if total == 0:
        return 0.0

    # Calculate entropy
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            prob = count / total
            entropy -= prob * np.log2(prob)

    # Normalize to 0-1 range (max entropy for 4 bases is 2)
    normalized_entropy = entropy / 2.0

    return normalized_entropy

def filter_sequence_by_entropy(
    sequence: str,
    window_size: int = 100,
    threshold: float = DEFAULT_ENTROPY_THRESHOLD,
    step_size: Optional[int] = None
) -> Tuple[bool, float]:
    """
    Check if a sequence contains low-complexity regions.

    Slides a window across the sequence and calculates entropy for each window.
    If any window falls below the threshold, the sequence is marked as low-complexity.

    Args:
        sequence: DNA sequence string
        window_size: Size of the sliding window in base pairs
        threshold: Minimum entropy threshold (default 0.8)
        step_size: Step size for sliding window (default: window_size // 2)

    Returns:
        Tuple of (is_high_complexity, min_entropy_found)
        - is_high_complexity: True if all windows meet the threshold
        - min_entropy_found: The lowest entropy value encountered
    """
    if step_size is None:
        step_size = max(1, window_size // 2)

    if len(sequence) < window_size:
        # If sequence is shorter than window, calculate entropy for entire sequence
        entropy = calculate_shannon_entropy(sequence)
        return entropy >= threshold, entropy

    min_entropy = 1.0
    is_high_complexity = True

    for i in range(0, len(sequence) - window_size + 1, step_size):
        window = sequence[i:i + window_size]
        entropy = calculate_shannon_entropy(window)
        min_entropy = min(min_entropy, entropy)

        if entropy < threshold:
            is_high_complexity = False
            # Early exit if we find a low-complexity region
            logger.debug(f"Low-complexity region found at position {i} with entropy {entropy:.4f}")
            break

    return is_high_complexity, min_entropy

def load_manifest(manifest_path: Path) -> Dict:
    """
    Load the data manifest JSON file.

    Args:
        manifest_path: Path to the manifest.json file

    Returns:
        Parsed manifest dictionary
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, 'r') as f:
        return json.load(f)

def filter_manifest_entries(
    manifest: Dict,
    threshold: float = DEFAULT_ENTROPY_THRESHOLD,
    sequence_field: str = 'sequence',
    output_path: Optional[Path] = None
) -> Dict:
    """
    Filter manifest entries based on sequence complexity.

    For each entry in the manifest that contains a sequence field,
    calculates the Shannon entropy and marks entries as 'filtered' if
    they contain low-complexity regions.

    Args:
        manifest: The data manifest dictionary
        threshold: Minimum entropy threshold (default 0.8)
        sequence_field: Name of the field containing the sequence
        output_path: Optional path to save the filtered manifest

    Returns:
        Updated manifest with complexity filtering results
    """
    filtered_count = 0
    total_count = 0

    if 'entries' not in manifest:
        logger.warning("Manifest does not contain 'entries' field. Skipping filtering.")
        return manifest

    for entry in manifest['entries']:
        if sequence_field not in entry:
            logger.debug(f"Skipping entry {entry.get('accession_id', 'unknown')}: no {sequence_field} field")
            continue

        total_count += 1
        sequence = entry[sequence_field]

        is_high_complexity, min_entropy = filter_sequence_by_entropy(
            sequence,
            window_size=100,
            threshold=threshold
        )

        entry['complexity'] = {
            'is_high_complexity': is_high_complexity,
            'min_entropy': round(min_entropy, 4),
            'threshold': threshold,
            'filtered': not is_high_complexity
        }

        if not is_high_complexity:
            filtered_count += 1
            logger.info(f"Filtered entry {entry.get('accession_id', 'unknown')}: "
                        f"min_entropy={min_entropy:.4f} < {threshold}")

    manifest['filtering_summary'] = {
        'total_entries_processed': total_count,
        'entries_filtered': filtered_count,
        'entries_retained': total_count - filtered_count,
        'threshold': threshold,
        'timestamp': str(Path.cwd().joinpath('filter_complexity.py').parent.parent.parent)
    }

    logger.info(f"Filtering complete: {filtered_count}/{total_count} entries filtered "
                f"(retained {total_count - filtered_count})")

    if output_path:
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Filtered manifest saved to {output_path}")

    return manifest

def main():
    """
    Main entry point for the low-complexity filtering utility.

    Reads data/manifest.json, filters entries based on sequence complexity,
    and outputs the filtered manifest to data/processed/filtered_manifest.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / 'data' / 'manifest.json'
    output_path = project_root / 'data' / 'processed' / 'filtered_manifest.json'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting low-complexity filtering for {manifest_path}")

    try:
        # Load manifest
        manifest = load_manifest(manifest_path)
        logger.info(f"Loaded manifest with {len(manifest.get('entries', []))} entries")

        # Filter entries
        filtered_manifest = filter_manifest_entries(
            manifest,
            threshold=DEFAULT_ENTROPY_THRESHOLD,
            output_path=output_path
        )

        logger.info("Low-complexity filtering completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Manifest file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during filtering: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
