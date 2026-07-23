"""
Mode Selector for determining pipeline execution mode.
Checks for pre-calculated VDOS/k availability and sets mode (Full vs. Structure-Only).
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from models.atomic_config import AtomicConfiguration
from logging_config import get_logger

logger = get_logger(__name__)


class ModeSelector:
    """
    Determines the execution mode of the pipeline based on data availability.

    Modes:
        - 'Full': Pre-calculated VDOS and thermal conductivity are available for all configs.
        - 'Structure-Only': VDOS/k data is missing; only topological analysis will be performed.
    """

    def __init__(self, raw_data_dir: Path, processed_dir: Path):
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_dir = Path(processed_dir)
        self.mode: Optional[str] = None
        self.reason: Optional[str] = None
        self.missing_vdos: List[str] = []

    def check_vdos_availability(self, config_ids: List[str]) -> Tuple[bool, List[str]]:
        """
        Check if pre-calculated VDOS data exists for the given configuration IDs.

        Args:
            config_ids: List of configuration IDs to check.

        Returns:
            Tuple (all_available, missing_ids).
        """
        missing_ids = []
        # Assuming VDOS files are stored in processed_dir with a naming convention
        # e.g., vdos_<config_id>.json or similar. Since the exact path isn't defined
        # in the prompt, we check a standard location or rely on a manifest.
        # For this implementation, we assume a file `vdos_manifest.json` exists in processed_dir
        # or we check individual files if the manifest is not present.

        vdos_manifest_path = self.processed_dir / "vdos_manifest.json"

        if vdos_manifest_path.exists():
            try:
                with open(vdos_manifest_path, 'r') as f:
                    manifest = json.load(f)
                available_ids = set(manifest.get("available_configs", []))
                for cid in config_ids:
                    if cid not in available_ids:
                        missing_ids.append(cid)
            except Exception as e:
                logger.error(f"Error reading VDOS manifest: {e}")
                missing_ids = config_ids # Assume all missing on error
        else:
            # Fallback: Check for individual files if no manifest exists
            # This is a heuristic and might need adjustment based on actual file structure
            for cid in config_ids:
                vdos_file = self.processed_dir / f"vdos_{cid}.json"
                if not vdos_file.exists():
                    missing_ids.append(cid)

        return len(missing_ids) == 0, missing_ids

    def determine_mode(self, config_ids: List[str]) -> str:
        """
        Determine the execution mode based on VDOS availability.

        Args:
            config_ids: List of configuration IDs from the raw data.

        Returns:
            'Full' or 'Structure-Only'.
        """
        all_available, missing_ids = self.check_vdos_availability(config_ids)
        self.missing_vdos = missing_ids

        if all_available:
            self.mode = "Full"
            self.reason = "Pre-calculated VDOS and thermal conductivity data available for all configurations."
            logger.info("Mode selected: Full")
        else:
            self.mode = "Structure-Only"
            self.reason = f"VDOS/k data missing for {len(missing_ids)} configurations. Switching to Structure-Only mode."
            logger.warning(f"Mode selected: Structure-Only. Missing {len(missing_ids)} configs.")

        return self.mode

    def save_mode_config(self, output_path: Optional[Path] = None) -> None:
        """
        Save the selected mode configuration to a JSON file.

        Args:
            output_path: Path to save the JSON. Defaults to processed_dir/mode_config.json.
        """
        if self.mode is None:
            raise RuntimeError("Mode has not been determined yet. Call determine_mode first.")

        if output_path is None:
            output_path = self.processed_dir / "mode_config.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            "mode": self.mode,
            "reason": self.reason,
            "missing_vdos_configs": self.missing_vdos,
            "timestamp": str(Path(__file__).stat().st_mtime) # Placeholder for real timestamp
        }

        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Mode configuration saved to {output_path}")


def check_mode_selector(config_ids: List[str], raw_data_dir: str, processed_dir: str) -> Dict[str, Any]:
    """
    Convenience function to run the mode selection logic.

    Args:
        config_ids: List of configuration IDs.
        raw_data_dir: Path to raw data directory.
        processed_dir: Path to processed data directory.

    Returns:
        Dictionary containing mode, reason, and missing configs.
    """
    selector = ModeSelector(Path(raw_data_dir), Path(processed_dir))
    mode = selector.determine_mode(config_ids)
    selector.save_mode_config()

    return {
        "mode": mode,
        "reason": selector.reason,
        "missing_vdos_configs": selector.missing_vdos
    }


def main():
    """Main entry point for mode selection script."""
    import sys
    from config.env_config import get_data_dir, get_processed_dir

    data_dir = get_data_dir()
    processed_dir = get_processed_dir()

    # In a real scenario, we would load config IDs from the raw data
    # For now, we assume an empty list or read from a specific file if available.
    # This is a placeholder to demonstrate the structure.
    # The actual list of config IDs would come from the download/validation step.
    config_ids = [] # To be populated by the pipeline

    if not config_ids:
        logger.warning("No configuration IDs provided. Mode selection skipped.")
        return

    result = check_mode_selector(config_ids, str(data_dir), str(processed_dir))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
