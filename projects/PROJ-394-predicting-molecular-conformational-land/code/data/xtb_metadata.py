"""
xtb Metadata Capture Module

Implements Constitution Principle VI: Capture, version, and archive the exact
xtb command-line flags, convergence criteria, and version info for every
calculation into data/calculation_metadata/.

This module ensures full reproducibility by logging the complete computational
provenance of every xtb run.
"""

import os
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import project utilities
from config import get_paths, get_hyperparams
from utils.logging import get_project_logger


class XtbMetadata:
    """
    Container and archiver for xtb calculation metadata.

    Captures:
    - Exact command-line invocation
    - xtb version information
    - Convergence criteria used
    - Timestamp and unique calculation ID
    - Input/output file paths
    - Hyperparameters from config
    """

    def __init__(
        self,
        smiles: str,
        calculation_id: Optional[str] = None,
        command_args: Optional[List[str]] = None,
        convergence_criteria: Optional[Dict[str, Any]] = None,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        energy: Optional[float] = None,
        gradient_norm: Optional[float] = None,
        converged: Optional[bool] = None,
        iterations: Optional[int] = None,
        wall_time: Optional[float] = None,
    ):
        """
        Initialize metadata for a single xtb calculation.

        Args:
            smiles: Input SMILES string
            calculation_id: Unique identifier (generated if not provided)
            command_args: List of command-line arguments passed to xtb
            convergence_criteria: Dict of convergence thresholds used
            input_file: Path to input geometry file
            output_file: Path to output results file
            energy: Final energy value (optional, filled post-calculation)
            gradient_norm: Final gradient norm (optional)
            converged: Whether optimization converged (optional)
            iterations: Number of optimization steps (optional)
            wall_time: Execution time in seconds (optional)
        """
        self.calculation_id = calculation_id or str(uuid.uuid4())
        self.smiles = smiles
        self.command_args = command_args or []
        self.convergence_criteria = convergence_criteria or {}
        self.input_file = input_file
        self.output_file = output_file
        self.energy = energy
        self.gradient_norm = gradient_norm
        self.converged = converged
        self.iterations = iterations
        self.wall_time = wall_time
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.logger = get_project_logger("xtb_metadata")

    def capture_xtb_version(self) -> str:
        """
        Query xtb for its version string.

        Returns:
            Version string from xtb --version, or 'unknown' if not found.

        Raises:
            RuntimeError: If xtb is not available in PATH.
        """
        try:
            result = subprocess.run(
                ["xtb", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            version = result.stdout.strip() or result.stderr.strip()
            if not version:
                version = "unknown"
            return version
        except FileNotFoundError:
            self.logger.error("xtb executable not found in PATH")
            raise RuntimeError("xtb executable not found in PATH. Please install xtb.")
        except subprocess.TimeoutExpired:
            self.logger.error("xtb --version timed out")
            raise RuntimeError("xtb version check timed out")

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary for JSON serialization."""
        return {
            "calculation_id": self.calculation_id,
            "smiles": self.smiles,
            "timestamp": self.timestamp,
            "xtb_version": self.capture_xtb_version(),
            "command_line": ["xtb"] + self.command_args,
            "command_args": self.command_args,
            "convergence_criteria": self.convergence_criteria,
            "input_file": self.input_file,
            "output_file": self.output_file,
            "results": {
                "energy": self.energy,
                "gradient_norm": self.gradient_norm,
                "converged": self.converged,
                "iterations": self.iterations,
                "wall_time_seconds": self.wall_time,
            },
            "config_snapshot": self._get_config_snapshot(),
        }

    def _get_config_snapshot(self) -> Dict[str, Any]:
        """Capture relevant hyperparameters from project config."""
        try:
            paths = get_paths()
            hyperparams = get_hyperparams()
            return {
                "data_dir": str(paths.data_dir),
                "output_dir": str(paths.output_dir),
                "xtb_threads": hyperparams.get("xtb_threads", "default"),
                "xtb_max_iterations": hyperparams.get("xtb_max_iterations", "default"),
                "xtb_convergence": hyperparams.get("xtb_convergence", "default"),
            }
        except Exception as e:
            self.logger.warning(f"Could not snapshot config: {e}")
            return {"error": str(e)}

    def save(self, output_dir: Optional[Path] = None) -> Path:
        """
        Save metadata to a JSON file in the calculation_metadata directory.

        Args:
            output_dir: Override default output directory (optional)

        Returns:
            Path to the saved metadata file

        Raises:
            RuntimeError: If directory creation fails or file write fails.
        """
        if output_dir is None:
            paths = get_paths()
            output_dir = paths.data_dir / "calculation_metadata"

        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self.calculation_id}.json"
        filepath = output_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, default=str)
            self.logger.info(f"Saved xtb metadata to {filepath}")
            return filepath
        except IOError as e:
            self.logger.error(f"Failed to write metadata file: {e}")
            raise RuntimeError(f"Failed to save metadata: {e}")


def get_xtb_version() -> str:
    """
    Utility function to get xtb version without creating a metadata object.

    Returns:
        Version string from xtb --version

    Raises:
        RuntimeError: If xtb is not available.
    """
    try:
        result = subprocess.run(
            ["xtb", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = result.stdout.strip() or result.stderr.strip()
        return version if version else "unknown"
    except FileNotFoundError:
        raise RuntimeError("xtb executable not found in PATH")
    except subprocess.TimeoutExpired:
        raise RuntimeError("xtb version check timed out")


def archive_calculation(
    smiles: str,
    command_args: List[str],
    convergence_criteria: Dict[str, Any],
    input_file: str,
    output_file: str,
    energy: Optional[float] = None,
    gradient_norm: Optional[float] = None,
    converged: Optional[bool] = None,
    iterations: Optional[int] = None,
    wall_time: Optional[float] = None,
    calculation_id: Optional[str] = None,
) -> Path:
    """
    Convenience function to create and save metadata in one call.

    Args:
        smiles: Input SMILES
        command_args: xtb command-line arguments
        convergence_criteria: Dict of convergence settings
        input_file: Input geometry path
        output_file: Output results path
        energy: Final energy
        gradient_norm: Final gradient norm
        converged: Convergence status
        iterations: Number of steps
        wall_time: Execution time
        calculation_id: Optional unique ID

    Returns:
        Path to saved metadata file
    """
    metadata = XtbMetadata(
        smiles=smiles,
        calculation_id=calculation_id,
        command_args=command_args,
        convergence_criteria=convergence_criteria,
        input_file=input_file,
        output_file=output_file,
        energy=energy,
        gradient_norm=gradient_norm,
        converged=converged,
        iterations=iterations,
        wall_time=wall_time,
    )
    return metadata.save()
