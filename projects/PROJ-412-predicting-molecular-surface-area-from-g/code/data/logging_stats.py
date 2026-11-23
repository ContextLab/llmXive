import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Import existing utilities to ensure we use the same logger
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback if run as script without package structure
    logging.basicConfig(level=logging.INFO)
    def get_logger(name: str):
        return logging.getLogger(name)

@dataclass
class ExcludedMolecule:
    """Represents a molecule that was excluded from processing."""
    smiles: str
    reason: str
    atom_count: Optional[int] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "smiles": self.smiles,
            "reason": self.reason,
            "atom_count": self.atom_count,
            "timestamp": self.timestamp
        }

@dataclass
class DatasetStatistics:
    """Aggregated statistics about the dataset processing."""
    total_input_molecules: int = 0
    valid_molecules: int = 0
    excluded_molecules: int = 0
    excluded_reasons: Dict[str, int] = field(default_factory=dict)
    max_atoms_limit: int = 100
    processing_start_time: Optional[str] = None
    processing_end_time: Optional[str] = None
    source_dataset: str = "unknown"
    output_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_input_molecules": self.total_input_molecules,
            "valid_molecules": self.valid_molecules,
            "excluded_molecules": self.excluded_molecules,
            "excluded_reasons": self.excluded_reasons,
            "max_atoms_limit": self.max_atoms_limit,
            "processing_start_time": self.processing_start_time,
            "processing_end_time": self.processing_end_time,
            "source_dataset": self.source_dataset,
            "output_file": self.output_file,
            "success_rate": round(self.valid_molecules / max(1, self.total_input_molecules), 4) if self.total_input_molecules > 0 else 0.0
        }

def log_excluded_molecule(logger: logging.Logger, molecule: ExcludedMolecule) -> None:
    """Log a single excluded molecule event."""
    logger.warning(
        f"Excluded molecule: SMILES={molecule.smiles[:50]}..., "
        f"Reason={molecule.reason}, "
        f"Atoms={molecule.atom_count}"
    )

def log_dataset_statistics(
    logger: logging.Logger, 
    stats: DatasetStatistics, 
    output_path: Optional[Path] = None
) -> None:
    """
    Log dataset statistics to the logger and optionally save to a JSON file.
    
    Args:
        logger: The logger instance to use
        stats: The DatasetStatistics object containing aggregated data
        output_path: Optional path to save the statistics as JSON
    """
    stats_dict = stats.to_dict()
    
    # Log summary to logger
    logger.info("=" * 60)
    logger.info("DATASET PROCESSING STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Source Dataset: {stats.source_dataset}")
    logger.info(f"Total Input Molecules: {stats.total_input_molecules:,}")
    logger.info(f"Valid Molecules: {stats.valid_molecules:,}")
    logger.info(f"Excluded Molecules: {stats.excluded_molecules:,}")
    logger.info(f"Success Rate: {stats_dict['success_rate']:.2%}")
    logger.info(f"Max Atoms Limit: {stats.max_atoms_limit}")
    
    if stats.excluded_reasons:
        logger.info("Exclusion Breakdown:")
        for reason, count in sorted(stats.excluded_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = (count / stats.excluded_molecules * 100) if stats.excluded_molecules > 0 else 0
            logger.info(f"  - {reason}: {count:,} ({pct:.1f}%)")
    
    logger.info(f"Processing Time: {stats.processing_end_time or 'N/A'}")
    logger.info(f"Output File: {stats.output_path or 'N/A'}")
    logger.info("=" * 60)
    
    # Save to JSON if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats_dict, f, indent=2)
        logger.info(f"Statistics saved to: {output_path}")

def log_split_statistics(
    logger: logging.Logger,
    train_size: int,
    test_size: int,
    val_size: Optional[int] = None,
    split_method: str = "stratified_by_mw",
    ks_p_value: Optional[float] = None
) -> None:
    """Log statistics about the data split."""
    total = train_size + test_size + (val_size or 0)
    
    logger.info("=" * 60)
    logger.info("DATA SPLIT STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Split Method: {split_method}")
    logger.info(f"Total Samples: {total:,}")
    logger.info(f"Training Set: {train_size:,} ({train_size/total*100:.1f}%)")
    logger.info(f"Test Set: {test_size:,} ({test_size/total*100:.1f}%)")
    if val_size:
        logger.info(f"Validation Set: {val_size:,} ({val_size/total*100:.1f}%)")
    
    if ks_p_value is not None:
        status = "PASSED" if ks_p_value > 0.05 else "FAILED"
        logger.info(f"KS Test (Train vs Test MW Distribution): p-value = {ks_p_value:.4f} [{status}]")
    
    logger.info("=" * 60)

def main():
    """
    Main entry point for standalone execution.
    Demonstrates the logging of excluded molecules and dataset statistics.
    """
    logger = get_logger(__name__)
    logger.setLevel(logging.INFO)
    
    # Example: Simulate processing statistics
    stats = DatasetStatistics(
        total_input_molecules=10000,
        valid_molecules=9250,
        excluded_molecules=750,
        excluded_reasons={
            "max_atoms_exceeded": 600,
            "invalid_smiles": 120,
            "valence_error": 30
        },
        max_atoms_limit=100,
        source_dataset="zinc15_streaming",
        output_file="data/processed/graphs_with_features.parquet"
    )
    
    # Log the statistics
    log_dataset_statistics(logger, stats, output_path=Path("results/reports/dataset_statistics.json"))
    
    # Example: Log an excluded molecule
    example_exclusion = ExcludedMolecule(
        smiles="CC(=O)Oc1ccccc1C(=O)O",
        reason="max_atoms_exceeded",
        atom_count=150
    )
    log_excluded_molecule(logger, example_exclusion)

if __name__ == "__main__":
    main()