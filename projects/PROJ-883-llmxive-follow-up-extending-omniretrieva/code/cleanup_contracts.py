"""
Cleanup utility for contract schema directory.
Removes stray duplicate schema files that may have been left over from earlier
iterations of the project (e.g., hyphenated versions).
"""
import pathlib
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    """
    Delete known duplicate schema files in the contracts directory.
    Currently removes:
      - statistics-result.schema.yaml
    """
    contracts_dir = pathlib.Path(__file__).resolve().parents[2] / "specs" / "001-structural-mismatch-cost" / "contracts"
    duplicates = [
        "statistics-result.schema.yaml",
    ]
    for fname in duplicates:
        target = contracts_dir / fname
        if target.exists():
            try:
                target.unlink()
                log.info(f"Removed duplicate schema file: {target}")
            except Exception as e:
                log.error(f"Failed to remove {target}: {e}")

if __name__ == "__main__":
    main()
