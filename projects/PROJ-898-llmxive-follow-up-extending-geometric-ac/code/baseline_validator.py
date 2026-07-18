import json
import logging
import os
import sys
from typing import Dict, Any, Tuple, List

# Ensure code/ is in path for imports when running as script
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from utils import setup_logging, compute_sha256

logger = logging.getLogger(__name__)

class BaselineValidator:
    """
    Validates the original GAM training metadata against the baseline file.
    Ensures the baseline file exists, is valid JSON, and contains required fields.
    Computes a checksum for the loaded metadata to be used in zero-overlap verification.
    """

    REQUIRED_FIELDS = [
        "dataset_name",
        "version",
        "description",
        "source",
        "statistics",
        "checksum",
        "created_at",
        "overlap_verification"
    ]

    def __init__(self, baseline_path: str = "data/raw/gam_baseline_metadata.json"):
        self.baseline_path = baseline_path
        self._metadata: Dict[str, Any] = {}
        self._is_valid: bool = False
        self._validation_errors: List[str] = []
        self._computed_hash: str = ""

    def ingest_and_validate(self) -> bool:
        """
        Loads the baseline metadata file and validates its structure.
        
        Returns:
            bool: True if validation passes, False otherwise.
        """
        self._validation_errors = []
        self._metadata = {}

        if not os.path.exists(self.baseline_path):
            self._validation_errors.append(f"Baseline file not found: {self.baseline_path}")
            logger.error(f"Baseline file not found: {self.baseline_path}")
            self._is_valid = False
            return False

        try:
            with open(self.baseline_path, 'r', encoding='utf-8') as f:
                self._metadata = json.load(f)
        except json.JSONDecodeError as e:
            self._validation_errors.append(f"Invalid JSON format: {str(e)}")
            logger.error(f"Invalid JSON format in {self.baseline_path}: {e}")
            self._is_valid = False
            return False
        except Exception as e:
            self._validation_errors.append(f"Error reading file: {str(e)}")
            logger.error(f"Error reading file {self.baseline_path}: {e}")
            self._is_valid = False
            return False

        # Validate required fields
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in self._metadata]
        if missing_fields:
            self._validation_errors.append(f"Missing required fields: {missing_fields}")
            logger.error(f"Missing required fields in baseline metadata: {missing_fields}")
            self._is_valid = False
            return False

        # Validate statistics structure
        stats = self._metadata.get("statistics", {})
        if "total_tasks" not in stats:
            self._validation_errors.append("Missing 'total_tasks' in statistics")
            logger.error("Missing 'total_tasks' in statistics")
            self._is_valid = False
            return False

        # Validate overlap_verification structure
        overlap = self._metadata.get("overlap_verification", {})
        required_overlap_keys = ["novel_kinematic_chains", "novel_materials", "novel_task_categories"]
        missing_overlap_keys = [k for k in required_overlap_keys if k not in overlap]
        if missing_overlap_keys:
            self._validation_errors.append(f"Missing overlap verification keys: {missing_overlap_keys}")
            logger.error(f"Missing overlap verification keys: {missing_overlap_keys}")
            self._is_valid = False
            return False

        # Compute checksum of the loaded metadata (excluding the checksum field itself for hashing)
        hashable_data = {k: v for k, v in self._metadata.items() if k != "checksum"}
        self._computed_hash = compute_sha256(json.dumps(hashable_data, sort_keys=True))
        
        self._is_valid = True
        logger.info(f"Baseline metadata validated successfully. Computed hash: {self._computed_hash}")
        return True

    @property
    def metadata(self) -> Dict[str, Any]:
        if not self._is_valid:
            raise RuntimeError("Metadata not valid. Call ingest_and_validate() first.")
        return self._metadata

    @property
    def computed_hash(self) -> str:
        if not self._is_valid:
            raise RuntimeError("Metadata not valid. Call ingest_and_validate() first.")
        return self._computed_hash

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    @property
    def validation_errors(self) -> List[str]:
        return self._validation_errors

    def get_baseline_summary(self) -> Dict[str, Any]:
        """Returns a summary of the baseline metadata."""
        if not self._is_valid:
            raise RuntimeError("Metadata not valid. Call ingest_and_validate() first.")
        
        stats = self._metadata.get("statistics", {})
        return {
            "dataset_name": self._metadata.get("dataset_name"),
            "version": self._metadata.get("version"),
            "total_tasks": stats.get("total_tasks"),
            "task_categories": stats.get("task_categories", []),
            "computed_hash": self._computed_hash
        }

def main():
    """Main entry point for standalone execution."""
    logging.basicConfig(level=logging.INFO)
    validator = BaselineValidator()
    
    if validator.ingest_and_validate():
        summary = validator.get_baseline_summary()
        print(f"Baseline Validation Successful:")
        print(f"  Dataset: {summary['dataset_name']}")
        print(f"  Version: {summary['version']}")
        print(f"  Total Tasks: {summary['total_tasks']}")
        print(f"  Computed Hash: {summary['computed_hash']}")
        return 0
    else:
        print("Baseline Validation Failed:")
        for error in validator.validation_errors:
            print(f"  - {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
