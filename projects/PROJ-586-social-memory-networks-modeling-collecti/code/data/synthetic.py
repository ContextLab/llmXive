"""Synthetic fallback generator for cue-response pairs.

Per FR-011, this module provides a fallback mechanism to generate synthetic
cue-response pairs when explicit cues are missing from the dataset.
IMPORTANT: This is a FALLBACK ONLY. It must NOT be used if real data is available.
The loader in `loaders.py` is responsible for ensuring this is only called
when the real dataset is genuinely unavailable.

NOTE: This module does NOT generate random/fake results for analysis. It generates
structural placeholder data (cues/responses) ONLY for the purpose of keeping the
simulation pipeline running when real data is missing. The actual metrics
(specialization, retrieval) are computed by the simulation logic over these
structural inputs, not pre-calculated fake numbers.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

# Seed for reproducibility in synthetic generation
SYNTHETIC_SEED = 42

@dataclass
class SyntheticDatasetSpec:
    """Specification for generating a synthetic dataset."""
    num_records: int = 10
    cue_length_range: tuple = (5, 15)
    response_length_range: tuple = (10, 30)
    seed: int = SYNTHETIC_SEED

def generate_synthetic_cue_response_pairs(spec: Optional[SyntheticDatasetSpec] = None) -> List[Dict[str, Any]]:
    """
    Generate a set of synthetic cue-response pairs.

    This function creates a minimal set of synthetic data (minimum 10 pairs)
    based on the provided specification. These pairs are designed to mimic
    the structure of real cue-response data for testing purposes when the
    real dataset is unavailable.

    IMPORTANT: This is a FALLBACK mechanism. It should only be invoked when
    the primary data source is genuinely unreachable.

    Args:
        spec: Optional specification for the synthetic dataset. If None, uses defaults.

    Returns:
        A list of synthetic records, each containing 'cue', 'response', and 'id'.
        Each record is marked with 'is_synthetic': True.
    """
    if spec is None:
        spec = SyntheticDatasetSpec()

    random.seed(spec.seed)
    records = []

    # Base vocabulary for generating synthetic text
    cues_base = [
        "Remember the fact about", "Recall the information regarding",
        "What do you know about", "Retrieve details on",
        "Summarize the knowledge concerning", "Identify the key point about",
        "Access the stored data on", "Bring to mind the fact that",
        "Recall the specific detail about", "Retrieve the memory of"
    ]

    topics = [
        "the capital of France", "the year World War II ended",
        "the chemical symbol for gold", "the largest planet in our solar system",
        "the author of Hamlet", "the boiling point of water",
        "the currency of Japan", "the longest river in the world",
        "the speed of light", "the smallest prime number"
    ]

    responses_base = [
        "The fact is well-established in historical records.",
        "This information is stored in the collective memory.",
        "The data indicates a clear pattern here.",
        "Based on available knowledge, the answer is clear.",
        "This is a fundamental piece of information.",
        "The memory trace for this is strong.",
        "Retrieved from the shared knowledge base.",
        "Confirmed by multiple sources.",
        "This fact has been verified and stored.",
        "The consensus is definitive on this point."
    ]

    for i in range(spec.num_records):
        cue = f"{random.choice(cues_base)} {random.choice(topics)}?"
        response = random.choice(responses_base)

        # Add some variation
        if random.random() > 0.5:
            response += f" (Confidence: {random.randint(80, 100)}%)"

        record = {
            "id": f"synthetic_{i:04d}",
            "cue": cue,
            "response": response,
            "is_synthetic": True,
            "source": "synthetic_fallback"
        }
        records.append(record)

    return records

def save_synthetic_dataset(records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the synthetic dataset to a JSON file.

    Args:
        records: List of synthetic records to save.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Compute checksum for reproducibility tracking
    content = json.dumps(records, indent=2, sort_keys=True)
    checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()

    manifest = {
        "source": "synthetic_fallback",
        "num_records": len(records),
        "checksum": checksum,
        "generated_at": "fallback_generation"
    }

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Save manifest alongside
    manifest_path = path.with_suffix('.manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

def generate_synthetic_dataset(spec: Optional[SyntheticDatasetSpec] = None, output_dir: str = "data/synthetic") -> str:
    """
    Generate and save a complete synthetic dataset.

    Args:
        spec: Optional specification for the dataset.
        output_dir: Directory to save the generated files.

    Returns:
        Path to the generated dataset file.
    """
    if spec is None:
        spec = SyntheticDatasetSpec()

    records = generate_synthetic_cue_response_pairs(spec)
    output_path = os.path.join(output_dir, "synthetic_cue_response.json")
    save_synthetic_dataset(records, output_path)
    return output_path

def verify_datasets() -> bool:
    """
    Verify that the synthetic fallback system is functional.

    Returns:
        True if the system is functional, False otherwise.
    """
    try:
        spec = SyntheticDatasetSpec(num_records=10)
        records = generate_synthetic_cue_response_pairs(spec)
        if len(records) < 10:
            return False
        # Verify structure
        for r in records:
            if not all(k in r for k in ['id', 'cue', 'response', 'is_synthetic']):
                return False
        return True
    except Exception:
        return False