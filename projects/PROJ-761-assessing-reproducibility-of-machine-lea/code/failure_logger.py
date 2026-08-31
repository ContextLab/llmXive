import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the failure reason enum-like class
class FailureReason:
    MODEL_SUBSTITUTION = "Model Substitution/Unavailable"
    DATA_GAP = "Data Unavailable"
    MISSING_SEED = "Missing Random Seed"
    PARAMETER_LIMIT_EXCEEDED = "Parameter Limit Exceeded (>1M)"
    MANIFEST_VALIDATION_ERROR = "Manifest Validation Error"
    DATASET_FETCH_ERROR = "Dataset Fetch Error"
    VARIABLE_MISMATCH = "Variable Mismatch"
    UNKNOWN = "Unknown Failure"

# File paths
FAILURE_LOG_PATH = Path("artifacts/logs/failure_log.json")
FAILURE_SUMMARY_PATH = Path("artifacts/logs/failure_summary.json")
FAILURE_REPORT_PATH = Path("artifacts/reports/failure_report.md")

def load_existing_failure_log() -> List[Dict[str, Any]]:
    """Load existing failure log from disk if it exists."""
    if FAILURE_LOG_PATH.exists():
        try:
            with open(FAILURE_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load existing failure log: {e}. Starting fresh.")
            return []
    return []

def record_failure(
    paper_id: str,
    reason: str,
    details: Optional[str] = None,
    source_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record a failure event for a specific paper.
    
    Args:
        paper_id: Unique identifier for the paper (e.g., DOI or repo ID)
        reason: The FailureReason constant describing the failure type
        details: Additional context about the failure
        source_file: The file or module where the failure originated
        
    Returns:
        The recorded failure entry
    """
    entry = {
        "paper_id": paper_id,
        "reason": reason,
        "details": details or "",
        "source_file": source_file or "unknown",
        "timestamp": datetime.now().isoformat()
    }
    
    # Load existing log, append, and save
    log = load_existing_failure_log()
    log.append(entry)
    
    # Ensure directory exists
    FAILURE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(FAILURE_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)
        
    logger.info(f"Recorded failure for paper {paper_id}: {reason}")
    return entry

def compile_failure_summary() -> Dict[str, Any]:
    """
    Compile a summary of all recorded failures.
    
    Returns:
        A dictionary containing counts by reason, list of affected papers,
        and total failure count.
    """
    log = load_existing_failure_log()
    
    if not log:
        return {
            "total_failures": 0,
            "by_reason": {},
            "affected_papers": [],
            "generated_at": datetime.now().isoformat()
        }
    
    # Count by reason
    reason_counts = {}
    affected_papers = set()
    
    for entry in log:
        reason = entry.get("reason", FailureReason.UNKNOWN)
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        affected_papers.add(entry.get("paper_id"))
    
    summary = {
        "total_failures": len(log),
        "by_reason": reason_counts,
        "affected_papers": sorted(list(affected_papers)),
        "generated_at": datetime.now().isoformat()
    }
    
    # Save summary
    FAILURE_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FAILURE_SUMMARY_PATH, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"Compiled failure summary: {summary['total_failures']} failures")
    return summary

def write_failure_report() -> str:
    """
    Generate a human-readable Markdown report of failures.
    
    Returns:
        Path to the generated report file
    """
    summary = compile_failure_summary()
    
    if summary["total_failures"] == 0:
        report_content = "# Failure Report\n\nNo failures recorded.\n"
    else:
        report_lines = [
            "# Qualitative Failure Report",
            "",
            f"**Generated**: {summary['generated_at']}",
            f"**Total Failures**: {summary['total_failures']}",
            "",
            "## Summary by Reason",
            ""
        ]
        
        # Add reason counts
        for reason, count in sorted(summary["by_reason"].items()):
            report_lines.append(f"- **{reason}**: {count}")
        
        report_lines.extend([
            "",
            "## Affected Papers",
            ""
        ])
        
        # Add affected papers
        for paper in summary["affected_papers"]:
            report_lines.append(f"- {paper}")
        
        # Add detailed log
        report_lines.extend([
            "",
            "## Detailed Failure Log",
            ""
        ])
        
        log = load_existing_failure_log()
        for entry in log:
            report_lines.append(f"### {entry['paper_id']}")
            report_lines.append(f"- **Reason**: {entry['reason']}")
            report_lines.append(f"- **Details**: {entry['details']}")
            report_lines.append(f"- **Source**: {entry['source_file']}")
            report_lines.append(f"- **Time**: {entry['timestamp']}")
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
    
    # Ensure directory exists
    FAILURE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(FAILURE_REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    logger.info(f"Written failure report to {FAILURE_REPORT_PATH}")
    return str(FAILURE_REPORT_PATH)

def main():
    """Main entry point for failure logging demonstration."""
    # Example usage
    logger.info("Starting failure logger demonstration...")
    
    # Record some sample failures
    record_failure(
        paper_id="10.1021/jacs.123456",
        reason=FailureReason.MODEL_SUBSTITUTION,
        details="Model had 2.5M parameters, exceeded 1M limit",
        source_file="model_runner.py"
    )
    
    record_failure(
        paper_id="10.1038/nature.789012",
        reason=FailureReason.DATA_GAP,
        details="Missing 'yield' column in dataset",
        source_file="ingest.py"
    )
    
    record_failure(
        paper_id="10.1016/j.chem.345678",
        reason=FailureReason.MISSING_SEED,
        details="No random seed specified in paper",
        source_file="model_runner.py"
    )
    
    # Compile and write report
    summary = compile_failure_summary()
    report_path = write_failure_report()
    
    print(f"Failure summary: {json.dumps(summary, indent=2)}")
    print(f"Report written to: {report_path}")

if __name__ == "__main__":
    main()
