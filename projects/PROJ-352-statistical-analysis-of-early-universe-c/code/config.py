"""
Configuration module for the CMB analysis project.
"""
import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json

@dataclass
class Config:
    """Project configuration."""
    paths: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Set default paths if not provided
        if not self.paths:
            self.paths = {
                "project_root": str(Path(__file__).parent.parent),
                "data_raw": str(Path(__file__).parent.parent / "data" / "raw"),
                "data_processed": str(Path(__file__).parent.parent / "data" / "processed"),
                "output": str(Path(__file__).parent.parent / "output"),
                "masked_map_path": str(Path(__file__).parent.parent / "data" / "processed" / "masked_cmb_n128.fits"),
                "mask_path": str(Path(__file__).parent.parent / "data" / "raw" / "galactic_mask.fits"),
                "mf_output_path": str(Path(__file__).parent.parent / "data" / "processed" / "minkowski_functionals_observed.json"),
                "checksum_report_path": str(Path(__file__).parent.parent / "data" / "raw" / "checksum_report.json"),
                "coverage_report_path": str(Path(__file__).parent.parent / "data" / "processed" / "coverage_report.json"),
                "map_stats_path": str(Path(__file__).parent.parent / "data" / "processed" / "map_stats.json"),
                "theoretical_genus_path": str(Path(__file__).parent.parent / "data" / "processed" / "theoretical_genus_curve.json"),
                "precision_report_path": str(Path(__file__).parent.parent / "data" / "processed" / "precision_report.json"),
                "results_path": str(Path(__file__).parent.parent / "output" / "results.json"),
                "mask_verification_log": str(Path(__file__).parent.parent / "data" / "processed" / "mask_verification.log"),
            }

_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def update_config(new_config: Dict[str, Any]):
    """Update the global configuration."""
    global _config
    if _config is None:
        _config = Config()
    if "paths" in new_config:
        _config.paths.update(new_config["paths"])
    if "parameters" in new_config:
        _config.parameters.update(new_config["parameters"])

def setup_logging():
    """Setup logging for the project."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    """Main entry point for configuration."""
    config = get_config()
    print("Project Configuration:")
    print(json.dumps(config.paths, indent=2))

if __name__ == "__main__":
    main()