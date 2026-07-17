import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
import time

# Import project utilities
from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir, get_results_dir

@dataclass
class ExcludedMolecule:
    """Data class to represent an excluded molecule with reasons."""
    smiles: str
    reason: str
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DatasetStatistics:
    """Data class to hold aggregate dataset statistics."""
    total_molecules: int = 0
    excluded_count: int = 0
    valid_count: int = 0
    avg_molecular_weight: float = 0.0
    min_molecular_weight: float = 0.0
    max_molecular_weight: float = 0.0
    avg_sasa: float = 0.0
    min_sasa: float = 0.0
    max_sasa: float = 0.0
    sasa_std: float = 0.0
    avg_node_count: float = 0.0
    avg_edge_count: float = 0.0
    failure_reasons: Dict[str, int] = field(default_factory=dict)
    processing_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary for JSON serialization."""
        return asdict(self)

def log_excluded_molecule(logger: logging.Logger, smiles: str, reason: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an excluded molecule to the logger and optionally to a dedicated log file.
    
    Args:
        logger: The logger instance to use.
        smiles: The SMILES string of the excluded molecule.
        reason: The reason for exclusion.
        metadata: Optional dictionary of additional metadata.
    """
    excluded = ExcludedMolecule(smiles=smiles, reason=reason, metadata=metadata or {})
    
    # Log to the main logger at WARNING level
    logger.warning(f"Excluded molecule: {smiles[:50]}... | Reason: {reason}")
    
    # Ensure the excluded molecules log file exists
    data_dir = get_data_dir()
    excluded_log_path = data_dir / "logs" / "excluded_molecules.jsonl"
    excluded_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to JSONL file
    with open(excluded_log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(asdict(excluded)) + '\n')

def log_dataset_statistics(logger: logging.Logger, stats: DatasetStatistics, output_file: Optional[Path] = None) -> None:
    """
    Log dataset statistics to the logger and save to a JSON file.
    
    Args:
        logger: The logger instance to use.
        stats: The DatasetStatistics object containing aggregate data.
        output_file: Optional path to save the statistics JSON file. Defaults to data/processed/dataset_statistics.json.
    """
    # Log summary to logger
    logger.info(f"Dataset Statistics Report:")
    logger.info(f"  Total Molecules Processed: {stats.total_molecules}")
    logger.info(f"  Valid Molecules: {stats.valid_count}")
    logger.info(f"  Excluded Molecules: {stats.excluded_count}")
    logger.info(f"  Exclusion Rate: {(stats.excluded_count / max(stats.total_molecules, 1)) * 100:.2f}%")
    logger.info(f"  Average Molecular Weight: {stats.avg_molecular_weight:.2f} Da")
    logger.info(f"  Average SASA: {stats.avg_sasa:.2f} Å²")
    logger.info(f"  Processing Time: {stats.processing_time_seconds:.2f} seconds")
    
    if stats.failure_reasons:
        logger.info("  Failure Reasons Breakdown:")
        for reason, count in stats.failure_reasons.items():
            logger.info(f"    - {reason}: {count}")
    
    # Save to JSON file
    if output_file is None:
        data_dir = get_data_dir()
        output_file = data_dir / "processed" / "dataset_statistics.json"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats.to_dict(), f, indent=2)
    
    logger.info(f"Dataset statistics saved to: {output_file}")

def log_split_statistics(logger: logging.Logger, split_counts: Dict[str, int], split_file: Optional[Path] = None) -> None:
    """
    Log statistics about the data split (train/test/val).
    
    Args:
        logger: The logger instance to use.
        split_counts: Dictionary mapping split name to count (e.g., {'train': 5000, 'test': 1000}).
        split_file: Optional path to the split file for reference.
    """
    total = sum(split_counts.values())
    logger.info("Data Split Statistics:")
    for split_name, count in split_counts.items():
        percentage = (count / max(total, 1)) * 100
        logger.info(f"  {split_name.capitalize()}: {count} ({percentage:.2f}%)")
    
    if split_file:
        logger.info(f"  Split indices saved to: {split_file}")

def main() -> None:
    """
    Main entry point for testing the logging statistics module.
    This function demonstrates the logging capabilities with sample data.
    """
    # Setup logging
    logger = get_logger(__name__, level=logging.INFO)
    
    logger.info("=== Dataset Statistics Logging Demo ===")
    
    # Simulate some dataset statistics
    stats = DatasetStatistics(
        total_molecules=10000,
        excluded_count=150,
        valid_count=9850,
        avg_molecular_weight=350.5,
        min_molecular_weight=50.0,
        max_molecular_weight=1200.0,
        avg_sasa=450.2,
        min_sasa=50.0,
        max_sasa=1500.0,
        sasa_std=120.5,
        avg_node_count=45.3,
        avg_edge_count=48.7,
        failure_reasons={
            "Invalid SMILES": 80,
            "Conformer Generation Failed": 50,
            "SASA Calculation Failed": 20
        },
        processing_time_seconds=3600.5
    )
    
    # Log the statistics
    log_dataset_statistics(logger, stats)
    
    # Simulate logging excluded molecules
    logger.info("\n--- Simulating Excluded Molecules ---")
    log_excluded_molecule(logger, "CCO", "Invalid SMILES")
    log_excluded_molecule(logger, "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC", "Molecule too large")
    
    # Simulate split statistics
    logger.info("\n--- Simulating Split Statistics ---")
    split_counts = {"train": 8000, "test": 1500, "val": 500}
    log_split_statistics(logger, split_counts)
    
    logger.info("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()