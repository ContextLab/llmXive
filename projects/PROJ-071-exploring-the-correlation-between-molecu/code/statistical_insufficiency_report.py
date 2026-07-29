"""
Task T021d: Statistical Insufficiency Report Generator.

Generates a markdown report documenting the statistical insufficiency
of the dataset when the Data Availability Gate or Sample Size check fails.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports if run as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from error_handlers import StatisticalInsufficiencyError
from config import get_config

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def generate_insufficiency_report(
    n_count: int, 
    reason: str, 
    gate_status_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate the statistical insufficiency report.
    
    Args:
        n_count: The number of records found.
        reason: The specific reason for insufficiency (e.g., "N < 30").
        gate_status_path: Path to the gate status JSON file to update.
        output_path: Path to write the markdown report.
        
    Returns:
        Path to the generated report.
    """
    project_root = get_project_root()
    
    # Default paths
    if output_path is None:
        output_path = str(project_root / "data" / "processed" / "statistical_insufficiency_report.md")
    
    if gate_status_path is None:
        gate_status_path = str(project_root / "data" / "gate_status.json")

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    timestamp = datetime.utcnow().isoformat()
    
    report_content = f"""# Statistical Insufficiency Report

**Generated:** {timestamp}
**Status:** HALTED

## Summary
The pipeline has halted due to statistical insufficiency in the dataset.

## Metrics
- **Record Count (N):** {n_count}
- **Minimum Required:** 30
- **Reason:** {reason}

## Analysis
The current dataset does not contain sufficient samples to perform valid statistical 
analysis (correlation/regression) with the required confidence levels. 

As per the project specification (FR-002, US2), a minimum of 30 samples is required 
for the stratified "Standard" condition subset to ensure statistical power.

## Decision
1. **Action Taken:** Analysis pipeline halted.
2. **Artifacts:** No regression models or correlation matrices were generated for this subset.
3. **Next Steps:** 
   - Review data ingestion sources.
   - Verify if additional data can be fetched from external degradation repositories.
   - If no additional data is available, the research goal is conditional on finding 
     a verified source of degradation data.

## Technical Details
- **Gate Status File:** `{gate_status_path}`
- **Report File:** `{output_path}`
- **Pipeline Phase:** User Story 2 (Standardization & Stratification)
"""

    # Write the report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Statistical insufficiency report generated: {output_path}")

    # Update gate status if path provided
    if gate_status_path:
        gate_status_dir = os.path.dirname(gate_status_path)
        if gate_status_dir:
            os.makedirs(gate_status_dir, exist_ok=True)
        
        gate_data = {
            "status": "FAIL",
            "reason": f"Statistical Insufficiency: {reason}",
            "n_count": n_count,
            "timestamp": timestamp,
            "report_path": output_path
        }
        
        with open(gate_status_path, 'w', encoding='utf-8') as f:
            json.dump(gate_data, f, indent=2)
        
        logger.info(f"Gate status updated to FAIL: {gate_status_path}")

    return output_path

def main():
    """
    Entry point for the script.
    Expects environment variables or arguments to define the failure context.
    For T021d, this is typically called when StatisticalInsufficiencyError is caught.
    """
    # Simulate the error context that would be passed from standardize.py
    # In a real run, these would be passed as arguments or read from a context file
    n_count = int(os.environ.get('INSUFFICIENT_N', 0))
    reason = os.environ.get('INSUFFICIENT_REASON', 'N < 30')
    
    if n_count < 30:
        report_path = generate_insufficiency_report(n_count, reason)
        print(f"Report generated: {report_path}")
    else:
        print("No insufficiency detected.")

if __name__ == "__main__":
    # Setup basic logging for script execution
    logging.basicConfig(level=logging.INFO)
    main()