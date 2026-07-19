"""
Logging utilities for tracking excluded molecules and dataset statistics.

This module provides classes and functions to log molecules excluded during
preprocessing (invalid SMILES, conformer generation failures) and to generate
comprehensive dataset statistics reports.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Import project utilities
from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir, get_results_dir


@dataclass
class ExcludedMolecule:
    """Dataclass to represent an excluded molecule entry."""
    smiles: str
    reason: str  # e.g., "invalid_smiles", "conformer_failed", "missing_weight"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetStatistics:
    """Dataclass to hold comprehensive dataset statistics."""
    total_input: int = 0
    valid_smiles: int = 0
    invalid_smiles: int = 0
    conformer_generated: int = 0
    conformer_failed: int = 0
    molecular_weight_calculated: int = 0
    final_dataset_size: int = 0
    exclusion_rate: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    failure_details: List[Dict[str, str]] = field(default_factory=list)
    mw_stats: Optional[Dict[str, float]] = None
    sasa_stats: Optional[Dict[str, float]] = None


def log_excluded_molecule(
    smiles: str,
    reason: str,
    details: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
) -> ExcludedMolecule:
    """
    Log an excluded molecule to the logger and return the data object.

    Args:
        smiles: The SMILES string of the molecule.
        reason: The reason for exclusion (e.g., 'invalid_smiles', 'conformer_failed').
        details: Optional dictionary with additional context.
        logger: Optional logger instance. If None, uses the default logger.

    Returns:
        ExcludedMolecule object representing the logged entry.
    """
    if logger is None:
        logger = get_logger(__name__)

    entry = ExcludedMolecule(smiles=smiles, reason=reason, details=details or {})
    logger.warning(f"Excluded molecule [{reason}]: {smiles[:50]}... | Details: {details}")
    return entry


def log_dataset_statistics(
    stats: DatasetStatistics,
    output_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log dataset statistics to a JSON file and the logger.

    Args:
        stats: DatasetStatistics object containing the statistics.
        output_path: Optional path to save the JSON report. Defaults to results/reports/dataset_stats.json.
        logger: Optional logger instance.
    """
    if logger is None:
        logger = get_logger(__name__)

    # Calculate exclusion rate if not set
    if stats.total_input > 0 and stats.exclusion_rate == 0.0:
        stats.exclusion_rate = (stats.invalid_smiles + stats.conformer_failed) / stats.total_input

    # Prepare log message
    log_msg = (
        f"Dataset Statistics Report:\n"
        f"  Total Input Molecules: {stats.total_input}\n"
        f"  Valid SMILES: {stats.valid_smiles}\n"
        f"  Invalid SMILES: {stats.invalid_smiles}\n"
        f"  Conformer Generated: {stats.conformer_generated}\n"
        f"  Conformer Failed: {stats.conformer_failed}\n"
        f"  Final Dataset Size: {stats.final_dataset_size}\n"
        f"  Exclusion Rate: {stats.exclusion_rate:.2%}"
    )

    if stats.mw_stats:
        log_msg += f"\n  MW Stats (Min/Max/Mean): {stats.mw_stats.get('min')}/{stats.mw_stats.get('max')}/{stats.mw_stats.get('mean')}"
    if stats.sasa_stats:
        log_msg += f"\n  SASA Stats (Min/Max/Mean): {stats.sasa_stats.get('min')}/{stats.sasa_stats.get('max')}/{stats.sasa_stats.get('mean')}"

    logger.info(log_msg)

    # Save to JSON if path provided or default
    if output_path is None:
        results_dir = get_results_dir()
        output_path = results_dir / "reports" / "dataset_stats.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert dataclass to dict for JSON serialization
    stats_dict = asdict(stats)
    # Handle nested None values properly
    if stats_dict['mw_stats'] is None:
        stats_dict['mw_stats'] = {}
    if stats_dict['sasa_stats'] is None:
        stats_dict['sasa_stats'] = {}

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats_dict, f, indent=2)

    logger.info(f"Dataset statistics saved to {output_path}")


def log_split_statistics(
    train_size: int,
    test_size: int,
    train_mw_mean: float,
    test_mw_mean: float,
    ks_p_value: float,
    split_valid: bool,
    output_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Log statistics about the data split.

    Args:
        train_size: Number of molecules in training set.
        test_size: Number of molecules in test set.
        train_mw_mean: Mean molecular weight of training set.
        test_mw_mean: Mean molecular weight of test set.
        ks_p_value: P-value from Kolmogorov-Smirnov test.
        split_valid: Whether the split passed validation (p > 0.05).
        output_path: Optional path to save the JSON report. Defaults to data/splits/split_report.json.
        logger: Optional logger instance.

    Returns:
        Dictionary containing the split statistics.
    """
    if logger is None:
        logger = get_logger(__name__)

    report = {
        "train_size": train_size,
        "test_size": test_size,
        "total_size": train_size + test_size,
        "train_mw_mean": train_mw_mean,
        "test_mw_mean": test_mw_mean,
        "mw_difference": abs(train_mw_mean - test_mw_mean),
        "ks_p_value": ks_p_value,
        "split_valid": split_valid,
        "timestamp": datetime.now().isoformat()
    }

    log_msg = (
        f"Split Statistics:\n"
        f"  Train Set: {train_size} molecules (MW Mean: {train_mw_mean:.2f})\n"
        f"  Test Set: {test_size} molecules (MW Mean: {test_mw_mean:.2f})\n"
        f"  KS Test P-Value: {ks_p_value:.4f} -> {'PASS' if split_valid else 'FAIL'}"
    )
    logger.info(log_msg)

    if output_path is None:
        data_dir = get_data_dir()
        output_path = data_dir / "splits" / "split_report.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Split report saved to {output_path}")
    return report


def main() -> None:
    """
    Main entry point for testing the logging utilities.
    This function demonstrates the usage of the logging functions.
    """
    logger = get_logger(__name__)
    logger.info("Running logging_stats module demo...")

    # Initialize statistics
    stats = DatasetStatistics()
    stats.total_input = 1000
    stats.valid_smiles = 950
    stats.invalid_smiles = 50
    stats.conformer_generated = 900
    stats.conformer_failed = 50
    stats.final_dataset_size = 900
    stats.mw_stats = {"min": 100.0, "max": 500.0, "mean": 250.0}
    stats.sasa_stats = {"min": 50.0, "max": 200.0, "mean": 120.0}

    # Log a few excluded molecules
    log_excluded_molecule("CCO", "invalid_smiles", {"error": "Sanitization failed"}, logger)
    log_excluded_molecule("CC(=O)O", "conformer_failed", {"error": "Max iterations exceeded"}, logger)

    # Log statistics
    log_dataset_statistics(stats, logger=logger)

    # Log split statistics
    log_split_statistics(
        train_size=720,
        test_size=180,
        train_mw_mean=248.5,
        test_mw_mean=252.1,
        ks_p_value=0.45,
        split_valid=True,
        logger=logger
    )

    logger.info("Demo completed successfully.")


if __name__ == "__main__":
    main()