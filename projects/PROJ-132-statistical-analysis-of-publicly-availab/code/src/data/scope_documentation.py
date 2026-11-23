import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Import from existing API surface
from src.config import setup_logging

logger = logging.getLogger(__name__)

def determine_scope_status(full_ebd_available: bool) -> Dict[str, Any]:
    """
    Determine the scope status based on the availability of the full EBD.
    
    Args:
        full_ebd_available: Boolean indicating if the full EBD was found.
        
    Returns:
        Dictionary containing scope status information.
    """
    if full_ebd_available:
        return {
            "source": "full_ebd_north_america_2020_2024",
            "reason": "Full EBD available via verified public URL",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    else:
        # Per plan and T005a result: full EBD unavailable, fallback to sample
        return {
            "source": "vvud/eb-data",
            "reason": "Full EBD unavailable",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

def write_scope_documentation(scope_status: Dict[str, Any], output_path: Path) -> None:
    """
    Write the scope documentation to a JSON file.
    
    Args:
        scope_status: Dictionary containing scope status information.
        output_path: Path to the output JSON file.
        
    Raises:
        FileNotFoundError: If the output directory does not exist.
        json.JSONEncodeError: If the scope_status cannot be serialized.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the scope documentation
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scope_status, f, indent=2)
    
    logger.info(f"Scope documentation written to {output_path}")

def run_scope_documentation_pipeline(full_ebd_available: bool, output_path: Optional[Path] = None) -> Path:
    """
    Run the scope documentation pipeline.
    
    Args:
        full_ebd_available: Boolean indicating if the full EBD was found.
        output_path: Optional path to the output JSON file. Defaults to data/provenance/scope_limitation.json.
        
    Returns:
        Path to the written scope documentation file.
    """
    if output_path is None:
        output_path = Path("data/provenance/scope_limitation.json")
    
    scope_status = determine_scope_status(full_ebd_available)
    write_scope_documentation(scope_status, output_path)
    
    return output_path

def main() -> None:
    """
    Main entry point for the scope documentation script.
    
    This script checks the availability of the full EBD (as determined by T005a)
    and documents the scope limitation if the full EBD is unavailable.
    
    Usage:
        python -m src.data.scope_documentation
        
    Environment:
        EXPECT_FULL_EBD_AVAILABLE: Optional environment variable to override the
        availability check. Set to 'true' or 'false'.
    """
    setup_logging()
    
    # Determine if full EBD is available
    # In a real run, this would come from T005a's result.
    # For this implementation, we check an environment variable or default to False
    # based on the project's known state (full EBD is not publicly available).
    import os
    env_flag = os.getenv("EXPECT_FULL_EBD_AVAILABLE", "").lower()
    if env_flag == "true":
        full_ebd_available = True
    elif env_flag == "false":
        full_ebd_available = False
    else:
        # Default to False as per project context (full EBD not available)
        full_ebd_available = False
    
    logger.info(f"Full EBD available: {full_ebd_available}")
    
    output_path = run_scope_documentation_pipeline(full_ebd_available)
    logger.info(f"Scope documentation pipeline completed. Output: {output_path}")

if __name__ == "__main__":
    main()
