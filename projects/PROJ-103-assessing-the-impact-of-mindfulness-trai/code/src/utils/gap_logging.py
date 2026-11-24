"""
Implementation of gap logging for dataset verification.
"""
from pathlib import Path
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def log_gap(dataset_id: str, reason: str) -> None:
    """
    Log a dataset gap to docs/gaps.md.
    
    Args:
        dataset_id: The OpenNeuro dataset identifier.
        reason: The reason for the gap (e.g., 'design_missing').
    """
    gap_file = Path("docs/gaps.md")
    gap_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize file if it doesn't exist
    if not gap_file.exists():
        gap_file.write_text("# Dataset Gaps\n\n| Dataset ID | Reason | Timestamp |\n|---|---|---|\n")
    
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    line = f"| {dataset_id} | {reason} | {timestamp} |\n"
    
    with open(gap_file, "a") as f:
        f.write(line)
    
    log.info(f"Logged gap for {dataset_id}: {reason}")
